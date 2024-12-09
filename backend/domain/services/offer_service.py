from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4, UUID
import structlog
from pytz import UTC
from enum import Enum

from backend.domain.entities.offer import Offer, OfferStatus, Currency, ValidationResult, BusinessRuleResult, OfferMetrics, GeographicRestriction, CostBreakdown
from backend.domain.entities.route import Route, TransportType
from backend.infrastructure.database.repositories.offer_repository import OfferRepository
from backend.infrastructure.external.ai_integration import AIIntegrationService
from .cost_calculation_service import CostCalculationService
from backend.infrastructure.ai.offer_insights import OfferInsightsService

logger = structlog.get_logger(__name__)

class OfferService:
    """Enhanced service for managing offers with comprehensive features."""
    
    def __init__(
        self,
        db_repository: OfferRepository,
        cost_service: CostCalculationService,
        ai_service: Optional[AIIntegrationService] = None,
        insights_service: Optional[OfferInsightsService] = None
    ):
        """Initialize the OfferService with required dependencies."""
        self.logger = logger.bind(service="OfferService")
        self.offer_repository = db_repository
        
        # Initialize cost service with required dependencies
        self.logger.info(
            "initializing_offer_service",
            cost_service_type=type(cost_service).__name__,
            ai_service_type=type(ai_service).__name__ if ai_service else None
        )
        
        if cost_service is None:
            # Since CostCalculationService needs its own dependencies, we should require it to be passed in
            raise ValueError("CostCalculationService must be provided")
        if not isinstance(cost_service, CostCalculationService):
            raise ValueError(f"Expected CostCalculationService but got {type(cost_service).__name__}")
        self.cost_service = cost_service
        
        # Initialize other services
        self.ai_service = ai_service or AIIntegrationService()
        self.insights_service = insights_service or OfferInsightsService()

    def generate_offer(
        self,
        route: Route,
        cost_settings: Dict[str, Any],
        margin_percentage: float = 10.0,
        currency: str = "EUR",
        client_id: Optional[UUID] = None,
        client_name: Optional[str] = None,
        client_contact: Optional[str] = None,
        geographic_restrictions: Optional[Dict[str, Any]] = None,
        user_id: str = "system"
    ) -> Offer:
        """Generate an enhanced offer with all features."""
        try:
            request_id = str(uuid4())
            start_time = datetime.now(UTC)
            
            self.logger.info(
                "generating_offer",
                request_id=request_id,
                route_id=str(route.id),
                margin=margin_percentage,
                currency=currency
            )

            # Calculate detailed costs
            costs = self.cost_service.calculate_route_cost(route=route, settings=cost_settings)
            
            # Calculate final price with margin
            margin_multiplier = 1 + (margin_percentage / 100)
            final_price = costs["cost_breakdown"]["total"] * margin_multiplier

            # Create CostBreakdown instance
            cost_breakdown = CostBreakdown(
                base_costs=costs["cost_breakdown"]["base_costs"],
                variable_costs=costs["cost_breakdown"]["variable_costs"],
                cargo_costs=costs["cost_breakdown"]["cargo_specific_costs"],
                total_cost=costs["cost_breakdown"]["total"],
                currency=Currency[currency]
            )

            # Extract all regions from the route's country segments
            regions = []
            if route.main_route and route.main_route.country_segments:
                regions.extend([seg.country for seg in route.main_route.country_segments])
            if route.empty_driving and route.empty_driving.country_segments:
                regions.extend([seg.country for seg in route.empty_driving.country_segments])
            regions = list(set(regions))  # Remove duplicates

            # Create geographic restrictions if provided
            geo_restrictions = None
            if geographic_restrictions:
                geo_restrictions = GeographicRestriction(
                    allowed_countries=geographic_restrictions.get('allowed_countries', []),
                    allowed_regions=geographic_restrictions.get('allowed_regions', []),
                    restricted_zones=geographic_restrictions.get('restricted_zones', [])
                )

            # Create the offer
            offer = Offer(
                id=uuid4(),
                route_id=route.id,
                client_id=client_id,
                client_name=client_name,
                client_contact=client_contact,
                cost_breakdown=cost_breakdown,
                margin_percentage=margin_percentage,
                final_price=final_price,
                currency=Currency[currency],
                status=OfferStatus.DRAFT,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                version=1,
                created_by=user_id,
                updated_by=user_id,
                geographic_restrictions=geo_restrictions,
                ai_insights=costs.get("optimization_insights", {}),
                applied_settings=cost_settings,
                business_rules_validation={}
            )

            # Save the offer with version history
            self._save_with_version_history(offer)
            
            # Log success metrics
            end_time = datetime.now(UTC)
            processing_time = (end_time - start_time).total_seconds() * 1000
            
            self.logger.info(
                "offer_generated",
                request_id=request_id,
                route_id=str(route.id),
                offer_id=str(offer.id),
                processing_time_ms=processing_time
            )
            
            return offer
            
        except Exception as e:
            self.logger.error(
                "offer_generation_failed",
                error=str(e),
                error_type=type(e).__name__,
                request_id=request_id,
                route_id=str(route.id),
                service="OfferService"
            )
            raise

    def get_offer(
        self,
        offer_id: UUID,
        include_settings: bool = False,
        include_history: bool = False,
        include_metrics: bool = False
    ) -> Optional[Offer]:
        """Get an offer by ID with optional includes."""
        try:
            offer = self.offer_repository.get_offer_by_id(offer_id)
            if not offer:
                return None

            if not include_settings:
                offer.applied_settings = {}
            if not include_history:
                offer._version_history = []
            if not include_metrics:
                offer._metrics = None

            return offer
        except Exception as e:
            self.logger.error("get_offer_failed", error=str(e), offer_id=str(offer_id))
            raise

    def update_offer(
        self,
        offer_id: UUID,
        updates: Dict[str, Any],
        user_id: str,
        reason: str
    ) -> Offer:
        """Update an offer with version tracking."""
        try:
            offer = self.get_offer(offer_id, include_settings=True, include_history=True)
            if not offer:
                raise ValueError(f"Offer {offer_id} not found")

            # Handle status transition
            if "status" in updates:
                new_status = OfferStatus(updates["status"])
                can_transition, message = offer.can_transition_to(new_status)
                if not can_transition:
                    raise ValueError(f"Invalid status transition: {message}")
                offer.status = new_status

            # Update other fields
            for field, value in updates.items():
                if field == "status":
                    continue
                if hasattr(offer, field):
                    setattr(offer, field, value)

            # Update metadata
            offer.updated_at = datetime.now(UTC)
            offer.updated_by = user_id

            # Validate the updated offer
            validation_results = offer.validate()
            if validation_results:
                error_validations = [v for v in validation_results if v.severity == "error"]
                if error_validations:
                    raise ValueError(f"Offer validation failed: {', '.join(v.message for v in error_validations)}")
                offer._validation_results = validation_results

            # Add version history
            offer.add_version(
                changed_by=user_id,
                changes=updates,
                reason=reason
            )

            # Save the updated offer
            self._save_with_version_history(offer)

            return offer
        except Exception as e:
            self.logger.error(
                "update_offer_failed",
                error=str(e),
                offer_id=str(offer_id)
            )
            raise

    def list_offers(
        self,
        filters: Dict[str, Any],
        include_settings: bool = False,
        include_history: bool = False,
        include_metrics: bool = False,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[Offer], int]:
        """List offers with enhanced filtering and optional includes."""
        try:
            self.logger.info("listing_offers", filters=filters)
            
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Apply filters with geographic restrictions
            offers, total = self.offer_repository.get_offers(
                start_date=filters.get('start_date'),
                end_date=filters.get('end_date'),
                min_price=filters.get('min_price'),
                max_price=filters.get('max_price'),
                status=filters.get('status'),
                currency=filters.get('currency'),
                countries=filters.get('countries'),
                regions=filters.get('regions'),
                client_id=filters.get('client_id'),
                limit=page_size,
                offset=offset
            )
            
            # Process includes
            for offer in offers:
                if not include_settings:
                    offer.applied_settings = {}
                if not include_history:
                    offer._version_history = []
                if not include_metrics:
                    offer._metrics = None

            return offers, total

        except Exception as e:
            self.logger.error("list_offers_failed", error=str(e))
            raise

    def list_offers_with_filters(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        status: Optional[str] = None,
        currency: Optional[str] = None,
        countries: Optional[List[str]] = None,
        regions: Optional[List[str]] = None,
        client_id: Optional[UUID] = None,
        limit: int = 10,
        offset: int = 0,
        include_settings: bool = False,
        include_history: bool = False,
        include_metrics: bool = False
    ) -> List[Offer]:
        """List offers with comprehensive filtering."""
        try:
            self.logger.info(
                "listing_offers_with_filters",
                filters={
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                    "min_price": min_price,
                    "max_price": max_price,
                    "status": status,
                    "currency": currency,
                    "countries": countries,
                    "regions": regions,
                    "client_id": str(client_id) if client_id else None
                }
            )

            # Get filtered offers from repository
            offers = self.offer_repository.list_offers(
                start_date=start_date,
                end_date=end_date,
                min_price=min_price,
                max_price=max_price,
                status=status,
                currency=currency,
                countries=countries,
                regions=regions,
                client_id=client_id,
                limit=limit,
                offset=offset
            )

            # Apply additional filters based on include flags
            for offer in offers:
                if not include_settings:
                    offer.applied_settings = {}
                if not include_history:
                    offer._version_history = []
                if not include_metrics:
                    offer._metrics = None
                else:
                    # Calculate metrics if requested
                    offer.calculate_metrics()

            return offers

        except Exception as e:
            self.logger.error(
                "list_offers_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    def count_offers_with_filters(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        status: Optional[str] = None,
        currency: Optional[str] = None,
        countries: Optional[List[str]] = None,
        regions: Optional[List[str]] = None,
        client_id: Optional[UUID] = None
    ) -> int:
        """Count total offers matching the filters."""
        try:
            return self.offer_repository.count_offers(
                start_date=start_date,
                end_date=end_date,
                min_price=min_price,
                max_price=max_price,
                status=status,
                currency=currency,
                countries=countries,
                regions=regions,
                client_id=client_id
            )
        except Exception as e:
            self.logger.error(
                "count_offers_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    def delete_offer(self, offer_id: UUID, user_id: str, reason: str) -> bool:
        """Soft delete an offer."""
        try:
            offer = self.get_offer(offer_id)
            if not offer:
                return False

            # Add version history for deletion
            offer.add_version(
                changed_by=user_id,
                changes={"action": "delete"},
                reason=reason
            )

            # Soft delete in repository
            success = self.offer_repository.soft_delete_offer(offer_id)
            
            if success:
                self.logger.info(
                    "offer_deleted",
                    offer_id=str(offer_id),
                    user_id=user_id,
                    reason=reason
                )
            
            return success

        except Exception as e:
            self.logger.error(
                "delete_offer_failed",
                error=str(e),
                offer_id=str(offer_id)
            )
            raise

    def _save_with_version_history(self, offer: Offer) -> None:
        """Save the offer and create a version history entry."""
        try:
            # First, save the offer
            offer_model = self.offer_repository.create({
                'id': offer.id,
                'route_id': offer.route_id,
                'client_id': offer.client_id,
                'cost_breakdown': offer.cost_breakdown.to_dict(),
                'margin_percentage': offer.margin_percentage,
                'final_price': offer.final_price,
                'currency': offer.currency,
                'status': offer.status,
                'version': offer.version,
                'created_at': offer.created_at,
                'updated_at': offer.updated_at,
                'offer_metadata': {
                    'client_name': offer.client_name,
                    'client_contact': offer.client_contact,
                    'geographic_restrictions': offer.geographic_restrictions.to_dict() if offer.geographic_restrictions else None,
                    'ai_insights': offer.ai_insights,
                    'applied_settings': offer.applied_settings,
                    'business_rules_validation': offer.business_rules_validation
                }
            })

            # Then create version history
            version_data = {
                'id': uuid4(),
                'entity_id': offer.id,  
                'version': offer.version,
                'data': {
                    'route_id': str(offer.route_id),
                    'client_id': str(offer.client_id) if offer.client_id else None,
                    'cost_breakdown': offer.cost_breakdown.to_dict(),
                    'margin_percentage': offer.margin_percentage,
                    'final_price': offer.final_price,
                    'currency': offer.currency.value if offer.currency else None,
                    'status': offer.status.value if offer.status else None,
                    'metadata': {
                        'client_name': offer.client_name,
                        'client_contact': offer.client_contact,
                        'geographic_restrictions': offer.geographic_restrictions.to_dict() if offer.geographic_restrictions else None,
                        'ai_insights': offer.ai_insights,
                        'applied_settings': offer.applied_settings,
                        'business_rules_validation': offer.business_rules_validation
                    }
                },
                'created_at': datetime.now(UTC),
                'created_by': offer.created_by,
                'change_reason': 'Initial offer creation',
                'version_metadata': {}
            }
            
            self.offer_repository.create_version(version_data)

            self.logger.info(
                "offer_saved_with_version",
                offer_id=str(offer.id),
                version=offer.version
            )

        except Exception as e:
            self.logger.error(
                "save_with_version_history_failed",
                error=str(e),
                error_type=type(e).__name__,
                offer_id=str(offer.id),
                version=offer.version
            )
            raise

    def _apply_business_rules(
        self,
        route: Route,
        costs: Dict[str, float],
        margin: float,
        currency: str,
        geographic_restrictions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """Apply business rules and return results."""
        rules = {
            "minimum_margin": margin >= 5.0,
            "maximum_margin": margin <= 50.0,
            "minimum_total_cost": costs["total_cost"] >= 100.0,
            "valid_currency": currency in [c.value for c in Currency],
            "route_exists": route is not None,
            "geographic_restrictions_valid": True
        }
        
        if geographic_restrictions:
            has_countries = bool(geographic_restrictions.get("allowed_countries"))
            has_regions = bool(geographic_restrictions.get("allowed_regions"))
            rules["geographic_restrictions_valid"] = has_countries or has_regions
        
        return rules
