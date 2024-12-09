import structlog
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
from enum import Enum
import json

logger = structlog.get_logger(__name__)

class MarketType(str, Enum):
    ORIGIN = "origin"
    TRANSIT = "transit"
    DESTINATION = "destination"

class MarketIndicator(str, Enum):
    DEMAND = "demand"
    SUPPLY = "supply"
    COMPETITION = "competition"
    SEASONALITY = "seasonality"
    PRICE_TREND = "price_trend"

class MarketInsight:
    def __init__(
        self,
        market_type: MarketType,
        region: str,
        indicators: Dict[MarketIndicator, float],
        metadata: Dict[str, Any]
    ):
        self.market_type = market_type
        self.region = region
        self.indicators = indicators
        self.metadata = metadata
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "market_type": self.market_type.value,
            "region": self.region,
            "indicators": {k.value: v for k, v in self.indicators.items()},
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }

class AIIntegrationService:
    """Service for AI-powered features like generating fun facts and insights."""
    
    def __init__(self):
        self.logger = logger.bind(service="AIIntegrationService")

    def analyze_market(
        self,
        region: str,
        market_type: MarketType,
        historical_data: Optional[Dict[str, Any]] = None
    ) -> MarketInsight:
        """
        Analyze market conditions for a specific region.
        In a real implementation, this would use historical data and ML models.
        """
        try:
            self.logger.info(
                "analyzing_market",
                region=region,
                market_type=market_type
            )
            
            # Simulate market analysis with mock data
            # In production, this would use real ML models and market data
            base_indicators = {
                MarketIndicator.DEMAND: 0.7,
                MarketIndicator.SUPPLY: 0.6,
                MarketIndicator.COMPETITION: 0.5,
                MarketIndicator.SEASONALITY: 0.8,
                MarketIndicator.PRICE_TREND: 0.6
            }
            
            # Adjust indicators based on market type
            if market_type == MarketType.ORIGIN:
                base_indicators[MarketIndicator.SUPPLY] += 0.2
            elif market_type == MarketType.DESTINATION:
                base_indicators[MarketIndicator.DEMAND] += 0.2
            elif market_type == MarketType.TRANSIT:
                base_indicators[MarketIndicator.COMPETITION] -= 0.1
            
            metadata = {
                "confidence_score": 0.85,
                "data_freshness": "recent",
                "market_volatility": "medium"
            }
            
            return MarketInsight(
                market_type=market_type,
                region=region,
                indicators=base_indicators,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(
                "market_analysis_failed",
                error=str(e),
                error_type=type(e).__name__,
                region=region,
                market_type=market_type
            )
            raise

    def get_comprehensive_insights(
        self,
        regions: List[str],
        distance_km: float,
        duration_hours: float,
        cost_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive insights combining market analysis and route metrics.
        """
        try:
            self.logger.info(
                "generating_comprehensive_insights",
                regions=regions,
                distance_km=distance_km,
                duration_hours=duration_hours
            )
            
            insights = {
                "markets": [],
                "route_metrics": {
                    "efficiency_score": min(0.9, distance_km / (duration_hours * 80)),  # 80 km/h as baseline
                    "cost_per_km": cost_data.get("total_cost", 0) / distance_km if distance_km > 0 else 0,
                    "time_efficiency": duration_hours / (distance_km / 60) if distance_km > 0 else 0  # 60 km/h as baseline
                },
                "recommendations": []
            }
            
            # Analyze each region
            for i, region in enumerate(regions):
                market_type = MarketType.TRANSIT
                if i == 0:
                    market_type = MarketType.ORIGIN
                elif i == len(regions) - 1:
                    market_type = MarketType.DESTINATION
                    
                market_insight = self.analyze_market(
                    region=region,
                    market_type=market_type
                )
                insights["markets"].append(market_insight.to_dict())
            
            # Generate recommendations based on insights
            insights["recommendations"] = self._generate_recommendations(
                market_insights=insights["markets"],
                route_metrics=insights["route_metrics"]
            )
            
            # Add metadata
            insights["metadata"] = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "version": "2.0",
                "confidence_score": 0.85
            }
            
            return insights
            
        except Exception as e:
            self.logger.error(
                "comprehensive_insights_generation_failed",
                error=str(e),
                error_type=type(e).__name__,
                regions=regions
            )
            raise

    def _generate_recommendations(
        self,
        market_insights: List[Dict[str, Any]],
        route_metrics: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on market insights and route metrics."""
        recommendations = []
        
        # Analyze market conditions
        for market in market_insights:
            market_type = market["market_type"]
            indicators = market["indicators"]
            
            if indicators["demand"] > 0.8:
                recommendations.append({
                    "type": "pricing",
                    "priority": "high",
                    "message": f"High demand in {market_type} market ({market['region']}). Consider increasing margins.",
                    "impact_score": 0.8
                })
            
            if indicators["competition"] > 0.7:
                recommendations.append({
                    "type": "strategy",
                    "priority": "medium",
                    "message": f"Strong competition in {market_type} market ({market['region']}). Consider service differentiation.",
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

    def generate_transport_fun_fact(
        self,
        origin: str,
        destination: str,
        distance_km: float
    ) -> Optional[str]:
        """
        Generate a fun fact about the transport route.
        For now, returns a simple static fact based on distance.
        In a real implementation, this would use an AI service.
        """
        try:
            self.logger.info(
                "generating_fun_fact",
                origin=origin,
                destination=destination,
                distance_km=distance_km
            )
            
            if distance_km < 100:
                return "Did you know? Short-distance transport routes often have the highest CO2 emissions per kilometer due to frequent stops and urban congestion!"
            elif distance_km < 500:
                return "Medium-distance routes like this one are optimal for hybrid and electric trucks, helping reduce environmental impact!"
            else:
                return "Long-distance routes like this contribute to about 30% of all road freight emissions in Europe. Using efficient route planning can help reduce this!"
                
        except Exception as e:
            self.logger.error(
                "fun_fact_generation_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return None
