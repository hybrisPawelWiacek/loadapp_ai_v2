import structlog
from typing import Optional

logger = structlog.get_logger(__name__)

class AIIntegrationService:
    """Service for AI-powered features like generating fun facts and insights."""
    
    def __init__(self):
        self.logger = logger.bind(service="AIIntegrationService")

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
