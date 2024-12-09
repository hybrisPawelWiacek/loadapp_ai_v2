from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4
import structlog
from pytz import UTC

from ..entities import Route, Offer
from ...infrastructure.database.repository import Repository
from ...infrastructure.external.ai_integration import AIIntegrationService

logger = structlog.get_logger(__name__)

class OfferService:
    def __init__(
        self,
        db_repository: Repository,
        ai_service: Optional[AIIntegrationService] = None
    ):
        self.logger = logger.bind(service="OfferService")
        self.db_repository = db_repository
        self.ai_service = ai_service or AIIntegrationService()

    def generate_offer(
        self,
        route: Route,
        cost_breakdown: Dict[str, float],
        margin_percentage: float = 10.0,
        currency: str = "EUR"
    ) -> Offer:
        """Generate an offer based on route, costs, and margin."""
        try:
            self.logger.info(
                "generating_offer",
                route_id=str(route.id),
                total_cost=cost_breakdown["total"],
                margin=margin_percentage
            )

            # Calculate final price with margin
            base_price = cost_breakdown["total"]
            margin_multiplier = 1 + (margin_percentage / 100)
            final_price = base_price * margin_multiplier

            # Generate fun fact using AI
            fun_fact = self.ai_service.generate_transport_fun_fact(
                origin=route.origin.address,
                destination=route.destination.address,
                distance_km=route.main_route.distance_km + route.empty_driving.distance_km
            )

            # Create offer
            offer = Offer(
                id=uuid4(),
                route_id=route.id,
                total_cost=cost_breakdown["total"],
                margin=margin_percentage,
                final_price=final_price,
                cost_breakdown=cost_breakdown,
                fun_fact=fun_fact,
                status="active",
                created_at=datetime.now(UTC)
            )

            # Save to database
            self.db_repository.save_offer(offer)

            self.logger.info(
                "offer_generated",
                offer_id=str(offer.id),
                final_price=final_price
            )

            return offer

        except Exception as e:
            self.logger.error(
                "offer_generation_failed",
                error=str(e),
                error_type=type(e).__name__,
                route_id=str(route.id)
            )
            raise

    def get_offer(self, offer_id: str) -> Optional[Offer]:
        """Retrieve an offer by ID."""
        try:
            return self.db_repository.get_offer(offer_id)
        except Exception as e:
            self.logger.error(
                "offer_retrieval_failed",
                error=str(e),
                error_type=type(e).__name__,
                offer_id=offer_id
            )
            raise

    def list_offers(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> list[Offer]:
        """List offers with pagination."""
        try:
            return self.db_repository.list_offers(limit, offset)
        except Exception as e:
            self.logger.error(
                "offer_listing_failed",
                error=str(e),
                error_type=type(e).__name__,
                limit=limit,
                offset=offset
            )
            raise
