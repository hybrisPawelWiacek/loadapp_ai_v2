import structlog
from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4, UUID
from datetime import timezone

from ...domain.entities.route import Route
from ...domain.entities.offer import Offer
from ...domain.services.cost_calculation_service import CostCalculationService
from ...domain.services.ai_integration_service import AIIntegrationService
from ...infrastructure.database.repository import Repository
from ...infrastructure.monitoring.decorators import measure_service_operation_time

logger = structlog.get_logger(__name__)

class OfferService:
    """Service for generating and managing offers."""
    
    def __init__(
        self,
        cost_service: CostCalculationService,
        ai_service: AIIntegrationService,
        repository: Repository,
        default_margin: float = 0.2  # 20% default margin
    ):
        self.cost_service = cost_service
        self.ai_service = ai_service
        self.repository = repository
        self.default_margin = default_margin
        self.logger = logger.bind(service="OfferService")

    @measure_service_operation_time(service="OfferService", operation="generate_offer")
    def generate_offer(
        self,
        route: Route,
        margin: Optional[float] = None
    ) -> Offer:
        """
        Generate an offer for a route.
        
        Args:
            route: Route object with all details
            margin: Optional margin override (default is 20%)
            
        Returns:
            Offer object with costs, margin, and fun fact
        """
        try:
            # Calculate costs
            cost_breakdown = self.cost_service.calculate_total_cost(route)
            total_cost = cost_breakdown["total_cost"]
            
            # Apply margin
            used_margin = margin if margin is not None else self.default_margin
            final_price = total_cost * (1 + used_margin)
            
            # Generate fun fact using AI
            fun_fact = self.ai_service.generate_transport_fun_fact(
                origin=route.origin.address,
                destination=route.destination.address,
                distance_km=route.main_route.distance_km
            )
            
            # Create offer
            offer = Offer(
                id=uuid4(),
                route_id=route.id,
                total_cost=total_cost,
                margin=used_margin * 100,  # Convert to percentage
                final_price=final_price,
                fun_fact=fun_fact or "Did you know? Transport is one of humanity's oldest industries!",
                status="pending",
                created_at=datetime.now(timezone.utc),
                cost_breakdown=cost_breakdown
            )
            
            # Save to database
            self.repository.save_offer(offer)
            
            self.logger.info(
                "offer_generated",
                offer_id=str(offer.id),
                route_id=str(route.id),
                total_cost=total_cost,
                margin=used_margin,
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

    @measure_service_operation_time(service="OfferService", operation="get_offer")
    async def get_offer(self, offer_id: UUID) -> Optional[Offer]:
        """Retrieve an offer by ID"""
        return await self.repository.get_offer(offer_id)

    @measure_service_operation_time(service="OfferService", operation="update_offer_status")
    async def update_offer_status(
        self,
        offer_id: UUID,
        status: str
    ) -> Optional[Offer]:
        """Update offer status (e.g., accepted, rejected)"""
        offer = await self.get_offer(offer_id)
        if not offer:
            return None
            
        offer.status = status
        await self.repository.save_offer(offer)
        return offer

    def calculate_margin_options(
        self,
        total_cost: float,
        steps: int = 3
    ) -> Dict[str, float]:
        """
        Calculate different margin options for price comparison.
        Returns a dict of margin percentages and final prices.
        """
        base_margin = self.default_margin
        margin_options = {}
        
        # Generate margin steps (e.g., 15%, 20%, 25%)
        for i in range(steps):
            margin = base_margin + (i - 1) * 0.05  # -5%, base%, +5%
            if margin > 0:  # Ensure no negative margins
                margin_options[f"{margin:.0%}"] = total_cost * (1 + margin)
                
        return margin_options
