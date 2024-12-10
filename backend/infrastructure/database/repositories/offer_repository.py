from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, desc

from backend.domain.entities.offer import Offer, OfferStatus, ValidationResult, BusinessRuleResult, OfferMetrics, GeographicRestriction
from backend.infrastructure.database.models import Offer as OfferModel, OfferVersionModel, OfferEventModel, CostSetting
from backend.infrastructure.logging import logger
from backend.infrastructure.serialization import json_dumps
from .versionable_repository import VersionableRepository

from dataclasses import dataclass

@dataclass
class OfferWithCosts:
    """Offer with detailed cost information."""
    offer: Offer
    cost_breakdown: Dict[str, float]
    applied_settings: List[Dict[str, Any]]

@dataclass
class OfferWithSettings:
    """Offer with applied settings information."""
    offer: Offer
    settings: List[Dict[str, Any]]
    route_settings: List[Dict[str, Any]]

class OfferRepository(VersionableRepository[OfferModel]):
    """Repository for managing offers in the database."""

    def __init__(self, session: Session):
        super().__init__(session, OfferModel, OfferVersionModel)
        self.logger = logger.bind(repository="OfferRepository")

    def _to_entity(self, model: OfferModel) -> Offer:
        """Convert database model to domain entity."""
        return Offer(
            id=UUID(model.id),
            route_id=UUID(model.route_id),
            total_cost=model.total_cost,
            margin=model.margin,
            final_price=model.final_price,
            fun_fact=model.fun_fact,
            status=model.status,
            created_at=model.created_at,
            cost_breakdown=model.cost_breakdown
        )

    def _to_model(self, entity: Offer) -> OfferModel:
        """Convert domain entity to database model."""
        return OfferModel(
            id=entity.id,  # Keep as UUID
            route_id=entity.route_id,  # Keep as UUID
            total_cost=entity.total_cost,
            margin=entity.margin,
            final_price=entity.final_price,
            fun_fact=entity.fun_fact,
            status=entity.status,
            created_at=entity.created_at,
            cost_breakdown=entity.cost_breakdown
        )

    def create(self, data: dict) -> OfferModel:
        """Create a new offer record."""
        try:
            # Ensure UUIDs are UUID objects
            if not isinstance(data['id'], UUID):
                data['id'] = UUID(data['id'])
            if not isinstance(data['route_id'], UUID):
                data['route_id'] = UUID(data['route_id'])
            if data.get('client_id') and not isinstance(data['client_id'], UUID):
                data['client_id'] = UUID(data['client_id'])
            
            # Convert string enums to enum objects
            if isinstance(data['currency'], str):
                data['currency'] = Currency[data['currency']]
            if isinstance(data['status'], str):
                data['status'] = OfferStatus[data['status']]

            offer_model = OfferModel(
                id=data['id'],
                route_id=data['route_id'],
                client_id=data.get('client_id'),
                cost_breakdown=data.get('cost_breakdown', {}),
                margin_percentage=data['margin_percentage'],
                final_price=data['final_price'],
                currency=data['currency'],
                status=data['status'],
                version=data.get('version', 1),
                is_deleted=data.get('is_deleted', False),
                created_at=data.get('created_at', datetime.utcnow()),
                updated_at=data.get('updated_at'),
                expires_at=data.get('expires_at'),
                offer_metadata=data.get('offer_metadata', {})
            )
            self.session.add(offer_model)
            self.session.commit()
            self.logger.info("offer_created", offer_id=str(data['id']))
            return offer_model
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error("offer_creation_failed", error=str(e), offer_id=str(data.get('id')))
            raise

    def get_by_id(self, offer_id: UUID) -> Optional[Offer]:
        """Retrieve an offer by its ID."""
        try:
            offer_model = self.session.query(OfferModel).filter(OfferModel.id == str(offer_id)).first()
            if offer_model is None:
                self.logger.info("offer_not_found", offer_id=str(offer_id))
                return None
            return self._to_entity(offer_model)
        except SQLAlchemyError as e:
            self.logger.error("offer_retrieval_failed", error=str(e), offer_id=str(offer_id))
            raise

    def update(self, offer: Offer) -> Optional[Offer]:
        """Update an existing offer."""
        try:
            offer_model = self.session.query(OfferModel).filter(OfferModel.id == str(offer.id)).first()
            if offer_model is None:
                self.logger.info("offer_not_found_for_update", offer_id=str(offer.id))
                return None

            # Update all fields
            offer_model.total_cost = offer.total_cost
            offer_model.margin = offer.margin
            offer_model.final_price = offer.final_price
            offer_model.fun_fact = offer.fun_fact
            offer_model.status = offer.status
            offer_model.cost_breakdown = offer.cost_breakdown

            self.session.commit()
            self.logger.info("offer_updated", offer_id=str(offer.id))
            return self._to_entity(offer_model)
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error("offer_update_failed", error=str(e), offer_id=str(offer.id))
            raise

    def delete(self, offer_id: UUID) -> bool:
        """Delete an offer by its ID."""
        try:
            result = self.session.query(OfferModel).filter(OfferModel.id == str(offer_id)).delete()
            self.session.commit()
            success = result > 0
            if success:
                self.logger.info("offer_deleted", offer_id=str(offer_id))
            else:
                self.logger.info("offer_not_found_for_deletion", offer_id=str(offer_id))
            return success
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error("offer_deletion_failed", error=str(e), offer_id=str(offer_id))
            raise

    def list_offers(
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
            limit: int = 100,
            offset: int = 0
        ) -> List[Offer]:
        """List offers with optional filtering and pagination.
        
        Args:
            start_date: Optional start date for filtering offers
            end_date: Optional end date for filtering offers
            min_price: Optional minimum final price
            max_price: Optional maximum final price
            status: Optional offer status filter
            currency: Optional currency filter
            countries: Optional list of countries
            regions: Optional list of regions
            client_id: Optional client ID filter
            limit: Maximum number of offers to return (default: 100)
            offset: Number of offers to skip (default: 0)
        
        Returns:
            List[Offer]: List of offers matching the filter criteria
            
        Raises:
            SQLAlchemyError: If there's a database error
        """
        try:
            query = self.session.query(OfferModel)
            filters_applied = []

            # Apply date range filters if provided
            if start_date:
                query = query.filter(OfferModel.created_at >= start_date)
                filters_applied.append("start_date")
            if end_date:
                query = query.filter(OfferModel.created_at <= end_date)
                filters_applied.append("end_date")

            # Apply price range filters if provided
            if min_price is not None:  # Allow 0 as a valid minimum price
                query = query.filter(OfferModel.final_price >= min_price)
                filters_applied.append("min_price")
            if max_price is not None:
                query = query.filter(OfferModel.final_price <= max_price)
                filters_applied.append("max_price")

            # Apply status filter if provided
            if status:
                query = query.filter(OfferModel.status == status)
                filters_applied.append("status")

            # Apply currency filter if provided
            if currency:
                query = query.filter(OfferModel.currency == currency)
                filters_applied.append("currency")

            # Apply geographic filters if provided
            if countries:
                query = query.filter(OfferModel.countries.overlap(countries))
                filters_applied.append("countries")
            if regions:
                query = query.filter(OfferModel.regions.overlap(regions))
                filters_applied.append("regions")

            # Apply client filter if provided
            if client_id:
                query = query.filter(OfferModel.client_id == str(client_id))
                filters_applied.append("client_id")

            # Log the applied filters
            self.logger.info("filters_applied", filters=filters_applied)

            # Count total results before pagination
            total_count = query.count()
            self.logger.debug("total_matching_offers", count=total_count)

            # Apply sorting - newest offers first
            query = query.order_by(desc(OfferModel.created_at))

            # Apply pagination
            # Note: SQLAlchemy optimizes this into a single query with LIMIT and OFFSET
            query = query.limit(limit).offset(offset)

            # Execute query and convert to entities
            offers = [self._to_entity(offer_model) for offer_model in query.all()]
            
            # Log the final results
            self.logger.info(
                "offers_retrieved",
                count=len(offers),
                total_matches=total_count,
                page_info={
                    "limit": limit,
                    "offset": offset,
                    "has_more": total_count > (offset + limit)
                }
            )
            
            return offers
            
        except SQLAlchemyError as e:
            self.logger.error(
                "offers_listing_failed",
                error=str(e),
                filters={
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                    "min_price": min_price,
                    "max_price": max_price,
                    "status": status,
                    "currency": currency,
                    "countries": countries,
                    "regions": regions,
                    "client_id": str(client_id) if client_id else None,
                    "limit": limit,
                    "offset": offset
                }
            )
            raise

    def get_by_route_id(self, route_id: UUID) -> List[Offer]:
        """Get all offers for a specific route."""
        try:
            offer_models = self.session.query(OfferModel).filter(OfferModel.route_id == str(route_id)).all()
            offers = [self._to_entity(model) for model in offer_models]
            self.logger.info("offers_retrieved_for_route", route_id=str(route_id), count=len(offers))
            return offers
        except SQLAlchemyError as e:
            self.logger.error("offers_retrieval_failed_for_route", error=str(e), route_id=str(route_id))
            raise

    def get_offer_with_costs(self, offer_id: UUID) -> Optional[OfferWithCosts]:
        """
        Get an offer with its detailed cost breakdown and applied cost settings.
        
        Args:
            offer_id: UUID of the offer to retrieve
            
        Returns:
            Optional[OfferWithCosts]: Offer with costs if found, None otherwise
            
        Raises:
            SQLAlchemyError: If there's a database error
        """
        try:
            # Query offer with eager loading of route relationship
            offer_model = (
                self.session.query(OfferModel)
                .filter(OfferModel.id == str(offer_id))
                .options(joinedload(OfferModel.route))
                .first()
            )
            
            if not offer_model:
                self.logger.info("offer_not_found", offer_id=str(offer_id))
                return None
                
            # Convert to domain entity
            offer = self._to_entity(offer_model)
            
            # Get cost breakdown from JSON field
            cost_breakdown = offer_model.cost_breakdown or {}
            
            # Get applied cost settings
            applied_settings = []
            if cost_breakdown:
                # Query cost settings for all cost types in the breakdown
                cost_settings = (
                    self.session.query(CostSetting)
                    .filter(
                        and_(
                            CostSetting.name.in_(cost_breakdown.keys()),
                            CostSetting.is_enabled == True
                        )
                    )
                    .all()
                )
                
                # Convert settings to dict format
                applied_settings = [
                    {
                        "name": setting.name,
                        "type": setting.type,
                        "category": setting.category,
                        "value": setting.value,
                        "multiplier": setting.multiplier,
                        "currency": setting.currency,
                        "description": setting.description
                    }
                    for setting in cost_settings
                ]
            
            self.logger.info(
                "offer_costs_retrieved",
                offer_id=str(offer_id),
                cost_count=len(cost_breakdown),
                settings_count=len(applied_settings)
            )
            
            return OfferWithCosts(
                offer=offer,
                cost_breakdown=cost_breakdown,
                applied_settings=applied_settings
            )
            
        except SQLAlchemyError as e:
            self.logger.error(
                "offer_costs_retrieval_failed",
                error=str(e),
                offer_id=str(offer_id)
            )
            raise

    def get_offer_with_settings(self, offer_id: UUID) -> Optional[OfferWithSettings]:
        """
        Get an offer with all its applied settings, including route-specific settings.
        
        Args:
            offer_id: UUID of the offer to retrieve
            
        Returns:
            Optional[OfferWithSettings]: Offer with settings if found, None otherwise
            
        Raises:
            SQLAlchemyError: If there's a database error
        """
        try:
            # Query offer with eager loading of route relationship
            offer_model = (
                self.session.query(OfferModel)
                .filter(OfferModel.id == str(offer_id))
                .options(joinedload(OfferModel.route))
                .first()
            )
            
            if not offer_model:
                self.logger.info("offer_not_found", offer_id=str(offer_id))
                return None
                
            # Convert to domain entity
            offer = self._to_entity(offer_model)
            
            # Get all enabled cost settings
            cost_settings = (
                self.session.query(CostSetting)
                .filter(CostSetting.is_enabled == True)
                .all()
            )
            
            # Convert settings to dict format
            settings = [
                {
                    "name": setting.name,
                    "type": setting.type,
                    "category": setting.category,
                    "value": setting.value,
                    "multiplier": setting.multiplier,
                    "currency": setting.currency,
                    "description": setting.description,
                    "last_updated": setting.last_updated.isoformat()
                }
                for setting in cost_settings
            ]
            
            # Get route-specific settings from route's JSON fields
            route_settings = []
            if offer_model.route:
                # Extract settings from route's transport_type and cargo
                if offer_model.route.transport_type:
                    route_settings.append({
                        "type": "transport",
                        "settings": offer_model.route.transport_type
                    })
                if offer_model.route.cargo:
                    route_settings.append({
                        "type": "cargo",
                        "settings": offer_model.route.cargo
                    })
            
            self.logger.info(
                "offer_settings_retrieved",
                offer_id=str(offer_id),
                settings_count=len(settings),
                route_settings_count=len(route_settings)
            )
            
            return OfferWithSettings(
                offer=offer,
                settings=settings,
                route_settings=route_settings
            )
            
        except SQLAlchemyError as e:
            self.logger.error(
                "offer_settings_retrieval_failed",
                error=str(e),
                offer_id=str(offer_id)
            )
            raise

    def create_offer(self, offer: Offer) -> Offer:
        """Create a new offer."""
        try:
            # Create offer model
            offer_model = OfferModel(
                id=offer.id,
                route_id=offer.route_id,
                total_cost=offer.total_cost,
                margin=offer.margin,
                final_price=offer.final_price,
                currency=offer.currency,
                status=offer.status,
                created_at=offer.created_at,
                updated_at=offer.updated_at,
                cost_breakdown=offer.cost_breakdown,
                applied_settings=offer.applied_settings,
                ai_insights=offer.ai_insights,
                version=offer.version,
                metadata=offer.metadata,
                geographic_restrictions=offer.geographic_restrictions.__dict__ if offer.geographic_restrictions else None,
                business_rules_validation=[rule.__dict__ for rule in offer.business_rules_validation],
                metrics=offer.metrics.__dict__ if offer.metrics else None
            )
            
            # Create initial version
            version_model = OfferVersionModel(
                offer_id=offer.id,
                version=1,
                data=offer.to_dict(),
                created_at=datetime.utcnow(),
                change_reason="Initial creation"
            )
            
            # Save both models
            self.session.add(offer_model)
            self.session.add(version_model)
            self.session.commit()
            
            return offer

        except Exception as e:
            self.session.rollback()
            self.logger.error("offer_creation_failed", error=str(e))
            raise

    def get_offer_by_id(self, offer_id: UUID) -> Optional[Offer]:
        """Retrieve an offer by ID."""
        try:
            offer_model = self.session.query(OfferModel).filter(
                OfferModel.id == offer_id
            ).first()
            
            if not offer_model:
                return None
                
            return self._model_to_entity(offer_model)

        except Exception as e:
            self.logger.error("offer_retrieval_failed", error=str(e))
            raise

    def update_offer(self, offer: Offer) -> Offer:
        """Update an existing offer."""
        try:
            # Get existing offer
            offer_model = self.session.query(OfferModel).filter(
                OfferModel.id == offer.id
            ).first()
            
            if not offer_model:
                raise ValueError(f"Offer with ID {offer.id} not found")
            
            # Update version
            offer.version += 1
            
            # Create new version record
            version_model = OfferVersionModel(
                offer_id=offer.id,
                version=offer.version,
                data=offer.to_dict(),
                created_at=datetime.utcnow(),
                change_reason="Update"  # This should come from business logic
            )
            
            # Update offer model
            for key, value in offer.to_dict().items():
                if hasattr(offer_model, key):
                    setattr(offer_model, key, value)
            
            # Save changes
            self.session.add(version_model)
            self.session.commit()
            
            return offer

        except Exception as e:
            self.session.rollback()
            self.logger.error("offer_update_failed", error=str(e))
            raise

    def delete_offer(self, offer_id: UUID) -> bool:
        """Delete an offer (soft delete)."""
        try:
            offer_model = self.session.query(OfferModel).filter(
                OfferModel.id == offer_id
            ).first()
            
            if not offer_model:
                return False
            
            # Implement soft delete by updating status
            offer_model.status = OfferStatus.EXPIRED
            offer_model.updated_at = datetime.utcnow()
            
            self.session.commit()
            return True

        except Exception as e:
            self.session.rollback()
            self.logger.error("offer_deletion_failed", error=str(e))
            raise

    def list_offers_with_filters(
        self,
        filters: Dict[str, Any],
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[List[Offer], int]:
        """List offers with filtering and pagination."""
        try:
            query = self.session.query(OfferModel)
            
            # Apply filters
            if filters.get('status'):
                query = query.filter(OfferModel.status == filters['status'])
            
            if filters.get('min_price'):
                query = query.filter(OfferModel.final_price >= filters['min_price'])
            
            if filters.get('max_price'):
                query = query.filter(OfferModel.final_price <= filters['max_price'])
            
            if filters.get('start_date'):
                query = query.filter(OfferModel.created_at >= filters['start_date'])
            
            if filters.get('end_date'):
                query = query.filter(OfferModel.created_at <= filters['end_date'])
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            query = query.order_by(desc(OfferModel.created_at))
            query = query.limit(limit).offset(offset)
            
            # Convert models to entities
            offers = [self._model_to_entity(model) for model in query.all()]
            
            return offers, total_count

        except Exception as e:
            self.logger.error("offer_listing_failed", error=str(e))
            raise

    def get_offer_history(self, offer_id: UUID) -> List[Dict[str, Any]]:
        """Get the version history of an offer."""
        try:
            versions = self.session.query(OfferVersionModel).filter(
                OfferVersionModel.offer_id == offer_id
            ).order_by(OfferVersionModel.version).all()
            
            return [
                {
                    "version": v.version,
                    "data": v.data,
                    "created_at": v.created_at.isoformat(),
                    "created_by": v.created_by,
                    "change_reason": v.change_reason
                }
                for v in versions
            ]

        except Exception as e:
            self.logger.error("offer_history_retrieval_failed", error=str(e))
            raise

    def record_event(
        self,
        offer_id: UUID,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """Record an event for an offer."""
        try:
            event = OfferEventModel(
                offer_id=offer_id,
                event_type=event_type,
                event_data=event_data,
                created_at=datetime.utcnow()
            )
            
            self.session.add(event)
            self.session.commit()

        except Exception as e:
            self.session.rollback()
            self.logger.error("offer_event_recording_failed", error=str(e))
            raise

    def create_version(self, version_data: dict) -> bool:
        """Create a new version record."""
        try:
            # Convert data to JSON string using custom serializer
            if 'data' in version_data:
                version_data['data'] = json_dumps(version_data['data'])
            if 'version_metadata' in version_data:
                version_data['version_metadata'] = json_dumps(version_data['version_metadata'])

            version_model = OfferVersionModel(**version_data)
            self.session.add(version_model)
            self.session.commit()
            self.logger.info(
                "offer_version_created",
                offer_id=version_data['entity_id'],
                version=version_data['version']
            )
            return True
        except Exception as e:
            self.session.rollback()
            self.logger.error(
                "offer_version_creation_failed",
                error=str(e),
                offer_id=version_data.get('entity_id'),
                repository="OfferRepository"
            )
            raise

    def _model_to_entity(self, model: OfferModel) -> Offer:
        """Convert a database model to a domain entity."""
        try:
            return Offer(
                id=model.id,
                customer_id=model.customer_id,
                route_id=model.route_id,
                cost_setting_id=model.cost_setting_id,
                status=OfferStatus(model.status),
                validation_result=ValidationResult(**model.validation_result) if model.validation_result else None,
                business_rule_result=BusinessRuleResult(**model.business_rule_result) if model.business_rule_result else None,
                metrics=OfferMetrics(**model.metrics) if model.metrics else None,
                geographic_restriction=GeographicRestriction(**model.geographic_restriction) if model.geographic_restriction else None,
                created_at=model.created_at,
                updated_at=model.updated_at,
                created_by=model.created_by,
                updated_by=model.updated_by,
                version=model.version
            )
        except Exception as e:
            self.logger.error(
                "model_to_entity_conversion_failed",
                error=str(e),
                offer_id=model.id if model else None,
                repository="OfferRepository"
            )
            raise

    def _entity_to_model(self, entity: Offer) -> OfferModel:
        """Convert a domain entity to a database model."""
        try:
            validation_result = json_dumps(entity.validation_result.__dict__) if entity.validation_result else None
            business_rule_result = json_dumps(entity.business_rule_result.__dict__) if entity.business_rule_result else None
            metrics = json_dumps(entity.metrics.__dict__) if entity.metrics else None
            geographic_restriction = json_dumps(entity.geographic_restriction.__dict__) if entity.geographic_restriction else None

            return OfferModel(
                id=entity.id,
                customer_id=entity.customer_id,
                route_id=entity.route_id,
                cost_setting_id=entity.cost_setting_id,
                status=entity.status.value,
                validation_result=validation_result,
                business_rule_result=business_rule_result,
                metrics=metrics,
                geographic_restriction=geographic_restriction,
                created_at=entity.created_at,
                updated_at=entity.updated_at,
                created_by=entity.created_by,
                updated_by=entity.updated_by,
                version=entity.version
            )
        except Exception as e:
            self.logger.error(
                "entity_to_model_conversion_failed",
                error=str(e),
                offer_id=entity.id if entity else None,
                repository="OfferRepository"
            )
            raise
