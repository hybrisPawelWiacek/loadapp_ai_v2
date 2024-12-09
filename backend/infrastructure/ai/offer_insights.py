from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import structlog
from enum import Enum
from datetime import datetime, timezone

class MarketType(Enum):
    ORIGIN = "origin"
    TRANSIT = "transit"
    DESTINATION = "destination"

class MarketIndicator(Enum):
    DEMAND_LEVEL = "demand_level"
    COMPETITION_LEVEL = "competition_level"
    PRICE_TREND = "price_trend"
    CAPACITY_UTILIZATION = "capacity_utilization"

@dataclass
class RouteInsight:
    """Represents a single AI-generated insight about a route or offer."""
    message: str
    confidence: float  # 0.0 to 1.0
    impact_level: str  # "low", "medium", "high"
    suggested_actions: List[str]
    metadata: Dict = field(default_factory=dict)

@dataclass
class MarketInsight:
    """Enhanced insight specifically for market analysis."""
    region: str
    market_type: MarketType
    indicators: Dict[str, float] = field(default_factory=dict)
    message: str = ""
    confidence: float = 0.8  # 0.0 to 1.0
    impact_level: str = "medium"  # "low", "medium", "high"
    suggested_actions: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

class OfferInsightsService:
    """
    Service for generating AI-powered insights about offers and routes.
    In production, this would integrate with actual AI models and services.
    """
    
    def __init__(
        self,
        model_endpoint: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        self.logger = structlog.get_logger(__name__)
        self.model_endpoint = model_endpoint
        self.api_key = api_key

    def get_comprehensive_insights(
        self,
        origin: str,
        destination: str,
        distance_km: float,
        duration_hours: float,
        cost_breakdown: Dict[str, float],
        route_type: str = "standard",
        regions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive insights about an offer and its route.
        
        Args:
            origin: Origin address/location
            destination: Destination address/location
            distance_km: Total distance in kilometers
            duration_hours: Total duration in hours
            cost_breakdown: Detailed cost breakdown
            route_type: Type of transport/route
            regions: List of regions/countries the route passes through
        
        Returns:
            Dict containing comprehensive insights including market analysis,
            route metrics, and recommendations.
        """
        try:
            if not regions:
                regions = []
            
            # Calculate route metrics
            route_metrics = {
                "efficiency_score": min(0.9, distance_km / (duration_hours * 80)),  # 80 km/h as baseline
                "cost_per_km": cost_breakdown.get("total_cost", 0) / max(1, distance_km),
                "time_efficiency": duration_hours / max(1, distance_km / 60)  # 60 km/h as baseline
            }
            
            # Generate market insights
            market_insights = self._analyze_market(regions, route_type)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                market_insights=market_insights,
                route_metrics=route_metrics,
                cost_breakdown=cost_breakdown
            )
            
            insights = {
                "markets": [insight.__dict__ for insight in market_insights],
                "route_metrics": route_metrics,
                "recommendations": recommendations,
                "metadata": {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "version": "2.0",
                    "confidence_score": 0.85
                }
            }
            
            self.logger.info(
                "generated_comprehensive_insights",
                total_markets=len(insights["markets"]),
                total_recommendations=len(recommendations)
            )
            
            return insights
            
        except Exception as e:
            self.logger.error(
                "insights_generation_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    def _analyze_market(
        self,
        regions: List[str],
        route_type: str
    ) -> List[MarketInsight]:
        """Generate comprehensive market insights for all regions in the route."""
        if not regions:
            return []

        insights = []
        
        # Analyze origin market
        insights.extend(self._analyze_origin_market(regions[0], route_type))
        
        # Analyze transit markets
        if len(regions) > 2:
            insights.extend(self._analyze_transit_markets(regions[1:-1], route_type))
        
        # Analyze destination market
        if len(regions) > 1:
            insights.extend(self._analyze_destination_market(regions[-1], route_type))
        
        return insights

    def _analyze_origin_market(
        self,
        region: str,
        route_type: str
    ) -> List[MarketInsight]:
        """Analyze market conditions at the origin."""
        return [MarketInsight(
            region=region,
            market_type=MarketType.ORIGIN,
            indicators={
                MarketIndicator.DEMAND_LEVEL.value: 0.8,
                MarketIndicator.COMPETITION_LEVEL.value: 0.6,
                MarketIndicator.PRICE_TREND.value: 0.7,
                MarketIndicator.CAPACITY_UTILIZATION.value: 0.75
            },
            message=f"Strong outbound demand from {region}",
            confidence=0.85,
            impact_level="high",
            suggested_actions=[
                "Consider increasing vehicle allocation in this region",
                "Evaluate potential for return loads"
            ],
            metadata={
                "market_volatility": "low",
                "data_freshness": "recent"
            }
        )]

    def _analyze_transit_markets(
        self,
        regions: List[str],
        route_type: str
    ) -> List[MarketInsight]:
        """Analyze market conditions in transit regions."""
        insights = []
        for region in regions:
            insights.append(MarketInsight(
                region=region,
                market_type=MarketType.TRANSIT,
                indicators={
                    MarketIndicator.DEMAND_LEVEL.value: 0.6,
                    MarketIndicator.COMPETITION_LEVEL.value: 0.5,
                    MarketIndicator.PRICE_TREND.value: 0.6,
                    MarketIndicator.CAPACITY_UTILIZATION.value: 0.5
                },
                message=f"Potential for additional cargo pickup in {region}",
                confidence=0.75,
                impact_level="medium",
                suggested_actions=[
                    f"Research cargo opportunities in {region}",
                    "Evaluate local partnerships"
                ],
                metadata={
                    "market_volatility": "medium",
                    "data_freshness": "recent"
                }
            ))
        return insights

    def _analyze_destination_market(
        self,
        region: str,
        route_type: str
    ) -> List[MarketInsight]:
        """Analyze market conditions at the destination."""
        return [MarketInsight(
            region=region,
            market_type=MarketType.DESTINATION,
            indicators={
                MarketIndicator.DEMAND_LEVEL.value: 0.85,
                MarketIndicator.COMPETITION_LEVEL.value: 0.7,
                MarketIndicator.PRICE_TREND.value: 0.8,
                MarketIndicator.CAPACITY_UTILIZATION.value: 0.9
            },
            message=f"High demand for {route_type} transport in {region}",
            confidence=0.9,
            impact_level="high",
            suggested_actions=[
                "Optimize pricing for return trips",
                "Establish local partnerships for consistent cargo availability"
            ],
            metadata={
                "market_volatility": "low",
                "data_freshness": "recent"
            }
        )]

    def _generate_recommendations(
        self,
        market_insights: List[MarketInsight],
        route_metrics: Dict[str, float],
        cost_breakdown: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on all insights."""
        recommendations = []
        
        # Analyze market conditions
        for insight in market_insights:
            indicators = insight.indicators
            
            if indicators.get(MarketIndicator.DEMAND_LEVEL.value, 0) > 0.8:
                recommendations.append({
                    "type": "pricing",
                    "priority": "high",
                    "message": f"High demand in {insight.market_type.value} market ({insight.region}). Consider increasing margins.",
                    "impact_score": 0.8
                })
            
            if indicators.get(MarketIndicator.COMPETITION_LEVEL.value, 0) > 0.7:
                recommendations.append({
                    "type": "strategy",
                    "priority": "medium",
                    "message": f"Strong competition in {insight.market_type.value} market ({insight.region}). Consider service differentiation.",
                    "impact_score": 0.6
                })
        
        # Analyze route efficiency
        if route_metrics["efficiency_score"] < 0.6:
            recommendations.append({
                "type": "operations",
                "priority": "high",
                "message": "Route efficiency below target. Consider route optimization or alternative transport modes.",
                "impact_score": 0.7
            })
        
        return recommendations
