from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID
from dataclasses import asdict

from backend.domain.entities import (
    Route, Location, TransportType, Cargo, CostSetting, MainRoute, EmptyDriving, CountrySegment,
    TimelineEvent, Offer, RouteSegment
)

class RoutePlanningService:
    def calculate_route(
        self,
        origin: Location,
        destination: Location,
        pickup_time: datetime,
        delivery_time: datetime,
        transport_type: Optional[TransportType] = None,
        cargo: Optional[Cargo] = None
    ) -> Route:
        """Calculate route between two points."""
        # Create route with default values for empty_driving and main_route
        empty_driving = EmptyDriving(
            distance_km=200.0,
            duration_hours=4.0,
            base_cost=75.0
        )
        
        main_route = MainRoute(
            distance_km=1000.0,
            duration_hours=10.0,
            country_segments=[CountrySegment(
                country="Germany",
                distance_km=1000.0,
                duration_hours=10.0
            )]
        )

        # Create timeline events
        timeline = [
            TimelineEvent(
                type="empty_driving_start",
                time=pickup_time,
                location=origin
            ),
            TimelineEvent(
                type="pickup",
                time=pickup_time,
                location=origin
            ),
            TimelineEvent(
                type="delivery",
                time=delivery_time,
                location=destination
            )
        ]

        route = Route(
            id=UUID(int=0),  # Will be replaced by database
            origin=origin,
            destination=destination,
            pickup_time=pickup_time,
            delivery_time=delivery_time,
            transport_type=transport_type,
            cargo=cargo,
            empty_driving=empty_driving,
            main_route=main_route,
            timeline=timeline,
            total_duration_hours=empty_driving.duration_hours + main_route.duration_hours
        )

        return route

class CostCalculationService:
    def calculate_total_cost(
        self,
        route: Route,
        cost_settings: Optional[List[CostSetting]] = None
    ) -> Dict:
        """Calculate total cost for a route."""
        if not cost_settings:
            # Use default cost settings if none provided
            cost_settings = [
                CostSetting(
                    type="distance",
                    category="variable",
                    base_value=1.5,
                    description="Cost per kilometer"
                ),
                CostSetting(
                    type="time",
                    category="variable",
                    base_value=50.0,
                    description="Cost per hour"
                ),
                CostSetting(
                    type="fixed",
                    category="fixed",
                    base_value=100.0,
                    description="Base fee"
                )
            ]

        total_cost = 0.0
        cost_breakdown = {}

        # Calculate costs for empty driving and main route
        for segment_name, segment in [("empty_driving", route.empty_driving), ("main_route", route.main_route)]:
            segment_cost = 0.0
            
            # Add base cost for the segment
            segment_cost += segment.base_cost if hasattr(segment, 'base_cost') else 0.0
            
            # Add variable costs based on distance and time
            for cost_setting in cost_settings:
                if not cost_setting.is_enabled:
                    continue

                if cost_setting.type == "distance":
                    segment_cost += segment.distance_km * cost_setting.base_value * cost_setting.multiplier
                elif cost_setting.type == "time":
                    segment_cost += segment.duration_hours * cost_setting.base_value * cost_setting.multiplier
                elif cost_setting.type == "fixed":
                    segment_cost += cost_setting.base_value * cost_setting.multiplier

            cost_breakdown[segment_name] = segment_cost
            total_cost += segment_cost

        cost_breakdown["total"] = total_cost
        return cost_breakdown

class OfferService:
    def __init__(self, repository, ai_service=None):
        self.repository = repository
        self.ai_service = ai_service
        self.cost_service = CostCalculationService()

    def generate_offer(self, route: Route, margin: float = 10.0) -> Offer:
        """Generate an offer for a route."""
        # Calculate costs
        cost_breakdown = self.cost_service.calculate_total_cost(route)
        total_cost = cost_breakdown["total"]
        
        # Calculate final price with margin
        final_price = total_cost * (1 + margin / 100)
        
        # Get fun fact from AI service if available
        fun_fact = None
        if self.ai_service:
            try:
                fun_fact = self.ai_service.get_fun_fact()
            except Exception as e:
                fun_fact = "Did you know? The first commercial truck was built in 1896!"
        
        # Create offer
        offer = Offer(
            route_id=route.id,
            total_cost=total_cost,
            margin=margin,
            final_price=final_price,
            cost_breakdown=cost_breakdown,
            fun_fact=fun_fact,
            status="pending"
        )

        # Save offer to database
        self.repository.save_offer(offer)

        return offer

    def get_historical_offers(self, limit: int = 10) -> List[Offer]:
        """Get historical offers."""
        return self.repository.get_offers(limit)
