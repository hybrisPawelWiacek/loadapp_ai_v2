from flask import Blueprint, jsonify
from flask_restful import Api
from typing import Dict, Any, List
from backend.services.cost_calculation_service import CostCalculationService
from backend.infrastructure.database.repository import Repository
from backend.infrastructure.database.db_setup import SessionLocal
from backend.infrastructure.database.models import CostItem
from backend.api.endpoints.cost_endpoint import CostEndpoint
from pydantic import BaseModel, Field, validator
import structlog
from uuid import uuid4
from datetime import datetime

logger = structlog.get_logger(__name__)

# Create Blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')
api = Api(api_bp)

# Pydantic models for request validation
class CostItemUpdate(BaseModel):
    name: str = Field(..., description="Name of the cost item")
    value: float = Field(..., description="Value of the cost item")
    type: str = Field(..., description="Type of cost (fuel, driver, toll, etc.)")
    category: str = Field(..., description="Category of cost (fixed, variable)")
    multiplier: float = Field(1.0, description="Multiplier to apply to the value")
    currency: str = Field("EUR", description="Currency of the cost value")
    is_enabled: bool = Field(True, description="Whether this cost item is enabled")
    description: str = Field(None, description="Description of the cost item")

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

# Register routes
api.add_resource(
    CostEndpoint, 
    '/costs',
    '/costs/<string:cost_id>',
    '/costs/settings',
    endpoint='cost_settings'
)
