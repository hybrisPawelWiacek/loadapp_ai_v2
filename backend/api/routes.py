from fastapi import FastAPI, HTTPException, Depends, Body
from typing import Dict, Any, List
from backend.services.cost_calculation_service import CostCalculationService
from backend.infrastructure.database.repository import Repository
from backend.infrastructure.database.db_setup import SessionLocal
from backend.infrastructure.database.models import CostSetting
from pydantic import BaseModel, Field, validator
import structlog
from uuid import uuid4
from datetime import datetime

logger = structlog.get_logger(__name__)
app = FastAPI()

# Pydantic models for request validation
class CostSettingUpdate(BaseModel):
    name: str = Field(..., description="Name of the cost setting")
    value: float = Field(..., description="Value of the cost setting")
    type: str = Field(..., description="Type of cost (fuel, driver, toll, etc.)")
    category: str = Field(..., description="Category of cost (fixed, variable)")
    multiplier: float = Field(1.0, description="Multiplier to apply to the value")
    currency: str = Field("EUR", description="Currency of the cost value")
    is_enabled: bool = Field(True, description="Whether this cost setting is enabled")
    description: str = Field(None, description="Description of the cost setting")

    @validator('value')
    def validate_value(cls, v):
        if v < 0:
            raise ValueError("Cost value cannot be negative")
        return v

    @validator('multiplier')
    def validate_multiplier(cls, v):
        if v < 0:
            raise ValueError("Multiplier cannot be negative")
        return v

    @validator('type')
    def validate_type(cls, v):
        valid_types = ['fuel', 'driver', 'toll', 'maintenance', 'insurance', 'overhead']
        if v not in valid_types:
            raise ValueError(f"Invalid cost type. Must be one of: {', '.join(valid_types)}")
        return v

    @validator('category')
    def validate_category(cls, v):
        valid_categories = ['fixed', 'variable']
        if v not in valid_categories:
            raise ValueError(f"Invalid category. Must be one of: {', '.join(valid_categories)}")
        return v

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize repository and services
repository = Repository(SessionLocal())
cost_calculation_service = CostCalculationService(repository)

@app.post("/costs/{route_id}")
async def calculate_costs_for_route(route_id: str, db: SessionLocal = Depends(get_db)) -> Dict[str, Any]:
    """
    Calculate costs for a given route ID and store them
    """
    try:
        # Get route data from repository
        route = repository.get_route(route_id)
        if not route:
            logger.error("route_not_found", route_id=route_id)
            raise HTTPException(status_code=404, detail=f"Route with ID {route_id} not found")

        # Calculate costs
        costs = cost_calculation_service.calculate_costs({
            'distance': getattr(route.main_route, 'distance', 0),
            'duration': getattr(route.main_route, 'duration', 0)
        })

        # Update route with calculated costs
        route.total_cost = costs['total_cost']
        route.cost_breakdown = costs['breakdown']
        repository.save_route(route)

        logger.info("costs_calculated", route_id=route_id, total_cost=costs['total_cost'])
        return costs

    except ValueError as e:
        logger.error("cost_calculation_validation_error", error=str(e), route_id=route_id)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("cost_calculation_failed", error=str(e), route_id=route_id)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/costs/settings")
async def get_cost_settings(db: SessionLocal = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Get all cost settings
    """
    try:
        settings = repository.get_enabled_cost_settings()
        return [setting.to_dict() for setting in settings]
    except Exception as e:
        logger.error("get_cost_settings_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/costs/settings")
async def update_cost_settings(
    settings: List[CostSettingUpdate],
    db: SessionLocal = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update cost settings
    """
    try:
        # Convert Pydantic models to CostSetting objects
        cost_settings = []
        for setting in settings:
            cost_setting = CostSetting(
                id=uuid4(),
                name=setting.name,
                value=setting.value,
                type=setting.type,
                category=setting.category,
                multiplier=setting.multiplier,
                currency=setting.currency,
                is_enabled=setting.is_enabled,
                description=setting.description,
                last_updated=datetime.utcnow()
            )
            cost_settings.append(cost_setting)

        # Bulk update settings
        success = repository.bulk_update_cost_settings(cost_settings)
        if success:
            # Refresh cost calculation service cache
            cost_calculation_service._load_cost_settings()
            logger.info("cost_settings_updated", count=len(settings))
            return {"message": f"Successfully updated {len(settings)} cost settings"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update cost settings")

    except ValueError as e:
        logger.error("cost_settings_validation_error", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("update_cost_settings_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}
