import os
from typing import Optional
import openai
import structlog
from functools import lru_cache

logger = structlog.get_logger(__name__)

class AIIntegrationService:
    def __init__(self, api_key: Optional[str] = None):
        self.logger = logger.bind(service="AIIntegrationService")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key and api_key is not None:  # Only raise if api_key was provided but invalid
            self.logger.warning("openai_api_key_not_found")
            raise ValueError("OpenAI API key not found in environment variables")
        elif self.api_key:  # Only set API key if we have one
            openai.api_key = self.api_key

    @lru_cache(maxsize=100)
    def generate_transport_fun_fact(
        self, 
        origin: str, 
        destination: str,
        distance_km: float
    ) -> Optional[str]:
        """Generate a fun fact about transport related to the route."""
        try:
            self.logger.info(
                "generating_fun_fact",
                origin=origin,
                destination=destination,
                distance=distance_km
            )

            if not self.api_key:
                return "Fun fact generation is disabled in test mode."

            prompt = f"""Generate a short, interesting fun fact about transportation or logistics 
            related to a route from {origin} to {destination} covering {distance_km} kilometers.
            The fact should be engaging and educational, focusing on historical, technological, 
            or cultural aspects of transportation. Keep it under 200 characters."""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a knowledgeable transport historian."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )

            fun_fact = response.choices[0].message.content.strip()
            
            self.logger.info(
                "fun_fact_generated",
                origin=origin,
                destination=destination,
                fun_fact=fun_fact
            )

            return fun_fact

        except Exception as e:
            self.logger.error(
                "fun_fact_generation_failed",
                error=str(e),
                origin=origin,
                destination=destination
            )
            return None

    def __call__(
        self, 
        origin: str, 
        destination: str, 
        distance_km: float
    ) -> Optional[str]:
        """Convenience method to call the service directly."""
        return self.generate_transport_fun_fact(origin, destination, distance_km)
