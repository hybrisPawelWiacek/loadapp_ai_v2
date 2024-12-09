from typing import Dict, Any, Optional
from datetime import datetime
from uuid import uuid4
from backend.infrastructure.database.repository import Repository
from backend.services.cost_calculation_service import CostCalculationService
import structlog
from backend.domain.entities import Offer

logger = structlog.get_logger(__name__)

class OfferService:
    def __init__(self, repository: Repository, cost_service: CostCalculationService):
        self.repository = repository
        self.cost_service = cost_service
        self.logger = structlog.get_logger(__name__)

    def create_offer(self, route_id: str, margin: float = 15.0) -> Optional[Dict[str, Any]]:
        """
        Create an offer for a route with the given margin.
        
        Args:
            route_id: ID of the route
            margin: Profit margin percentage (default 15%)
            
        Returns:
            Dict containing the offer details or None if creation fails
            
        Raises:
            ValueError: If margin is invalid or route is not found
        """
        try:
            # Validate margin
            if not 0 <= margin <= 100:
                raise ValueError(f"Margin must be between 0 and 100, got {margin}")

            # Get route data
            route = self.repository.get_route(route_id)
            if not route:
                raise ValueError(f"Route with ID {route_id} not found")

            # Calculate costs if not already present
            if not hasattr(route, 'cost_breakdown') or not route.cost_breakdown:
                costs = self.cost_service.calculate_costs({
                    'distance': getattr(route.main_route, 'distance', 0),
                    'duration': getattr(route.main_route, 'duration', 0)
                })
                route.cost_breakdown = costs['breakdown']
                route.total_cost = costs['total_cost']
                self.repository.save_route(route)

            # Calculate offer price with margin
            base_price = route.total_cost
            margin_multiplier = 1 + (margin / 100)
            offer_price = base_price * margin_multiplier

            # Create offer object
            offer = Offer(
                id=str(uuid4()),
                route_id=route_id,
                created_at=datetime.utcnow(),
                base_cost=base_price,
                margin_percentage=margin,
                total_price=offer_price,
                cost_breakdown=route.cost_breakdown,
                status="pending",
                currency="EUR"
            )

            # Save offer to database
            saved_offer = self.repository.save_offer(offer)
            
            self.logger.info(
                "offer_created",
                offer_id=saved_offer.id,
                route_id=route_id,
                base_cost=base_price,
                margin=margin,
                total_price=offer_price
            )

            return {
                "id": saved_offer.id,
                "route_id": route_id,
                "base_cost": base_price,
                "margin_percentage": margin,
                "total_price": offer_price,
                "cost_breakdown": route.cost_breakdown,
                "status": "pending",
                "currency": "EUR",
                "created_at": saved_offer.created_at.isoformat()
            }

        except ValueError as e:
            self.logger.error(
                "offer_creation_validation_error",
                error=str(e),
                route_id=route_id,
                margin=margin
            )
            raise

        except Exception as e:
            self.logger.error(
                "offer_creation_failed",
                error=str(e),
                route_id=route_id,
                margin=margin
            )
            return None
