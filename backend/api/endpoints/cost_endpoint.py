from flask import request, jsonify
from flask_restful import Resource
import structlog
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from uuid import UUID

from ...domain.services.cost_calculation_service import CostCalculationService, CostCalculationError, RouteValidationError
from ...domain.services.cost_optimization_service import CostOptimizationService
from ...domain.services.cost_settings_service import CostSettingsService
from ...domain.validators.cost_setting_validator import CostSettingValidator
from ...domain.entities.route import Route
from ...infrastructure.database.repositories.base_repository import BaseRepository
from ...infrastructure.database.repositories.cost_setting_repository import CostSettingsRepository
from ...infrastructure.database.repositories.route_repository import RouteRepository
from ...infrastructure.database.session import SessionLocal
from ...infrastructure.database.models.cost_setting import CostSetting, CostSettingModel
from ...infrastructure.database.models.route import RouteModel
from ...infrastructure.monitoring.metrics_service import MetricsService

logger = structlog.get_logger(__name__)

class CostEndpoint(Resource):
    def __init__(self, repository: Optional[BaseRepository] = None, 
                 metrics_service: Optional[MetricsService] = None,
                 cost_settings_repository: Optional[CostSettingsRepository] = None,
                 cost_calculation_service: Optional[CostCalculationService] = None,
                 cost_optimization_service: Optional[CostOptimizationService] = None,
                 route_repository: Optional[RouteRepository] = None):
        """Initialize the CostEndpoint with optional dependencies."""
        super().__init__()
        
        # Create a new database session
        db_session = SessionLocal()
        
        # Initialize repositories
        if repository is None:
            self.repository = BaseRepository(db_session, CostSettingModel)
        else:
            self.repository = repository
            
        if cost_settings_repository is None:
            self.cost_settings_repository = CostSettingsRepository(db_session)
        else:
            self.cost_settings_repository = cost_settings_repository

        if route_repository is None:
            self.route_repository = RouteRepository(db_session)
        else:
            self.route_repository = route_repository
            
        # Initialize services
        self.metrics_service = metrics_service or MetricsService()
        self.cost_validator = CostSettingValidator()
        
        # Initialize cost optimization service
        if cost_optimization_service is None:
            self.cost_optimization_service = CostOptimizationService(
                metrics_service=self.metrics_service
            )
        else:
            self.cost_optimization_service = cost_optimization_service
        
        # Initialize cost calculation service
        if cost_calculation_service is None:
            self.cost_calculation_service = CostCalculationService(
                cost_settings_repository=self.cost_settings_repository,
                metrics_service=self.metrics_service,
                cost_optimization_service=self.cost_optimization_service
            )
        else:
            self.cost_calculation_service = cost_calculation_service
        
        # Initialize cost settings service
        self.cost_settings_service = CostSettingsService(
            repository=self.repository,
            validator=self.cost_validator,
            metrics_service=self.metrics_service
        )
        
        self.logger = logger.bind(
            endpoint="cost_endpoint",
            method=request.method if request else None
        )
        self.logger.info("cost_endpoint_initialized")

    def get(self, path: str = None):
        """Get cost settings or specific cost details."""
        logger.info("cost_endpoint_get_called",
                   endpoint="cost_endpoint",
                   method="GET",
                   path=path)
        
        try:
            if path is None or path == 'settings':
                # Return all cost settings
                settings = self.cost_settings_repository.get_all()
                return {
                    "settings": [setting.to_dict() for setting in settings],
                    "total": len(settings)
                }
            elif path == 'defaults':
                defaults = self.cost_settings_service.get_default_settings()
                return jsonify([setting.to_dict() for setting in defaults])
                
            elif path == 'analysis':
                # Get current settings for analysis
                settings = self.cost_settings_service.get_all_settings()
                analysis = self.cost_optimization_service.analyze_cost_patterns(settings)
                return jsonify(analysis)
                
            elif path == 'optimization':
                settings = self.cost_settings_service.get_all_settings()
                suggestions = self.cost_optimization_service.suggest_optimizations(settings)
                return jsonify(suggestions)
                
            else:
                self.logger.error("invalid_path", path=path)
                return {"error": "Invalid endpoint path"}, 404
                
        except Exception as e:
            self.logger.error("get_request_failed",
                            path=path,
                            error=str(e),
                            error_type=type(e).__name__)
            return {"error": f"Failed to process request: {str(e)}"}, 500

    def post(self, path: str = None, cost_id: str = None):
        """
        Handle POST requests for cost endpoints.
        
        Endpoints:
        - /costs/settings: Update cost settings
        - /costs/<cost_id>: Calculate costs for a specific route
        """
        try:
            self.logger.info("cost_endpoint_post_called", path=path, cost_id=cost_id)
            
            if cost_id:
                return self._calculate_route_cost(cost_id)
            elif path == 'settings':
                # Parse and validate request data
                if not request.is_json:
                    return {"error": "Request must be JSON"}, 400
                    
                data = request.get_json()
                if not isinstance(data, list):
                    return {"error": "Request body must be a list of cost settings"}, 400
                    
                # Convert JSON to CostSetting objects
                try:
                    settings = [CostSetting(**setting_data) for setting_data in data]
                except Exception as e:
                    self.logger.error("invalid_settings_format", error=str(e))
                    return {"error": f"Invalid settings format: {str(e)}"}, 400
                
                # Update settings
                result = self.cost_settings_service.update_settings(settings)
                return jsonify({"message": "Settings updated successfully", "updated": len(result)}), 200
            else:
                self.logger.error("invalid_post_path", path=path)
                return {"error": "Invalid endpoint for POST request"}, 404
                
        except Exception as e:
            self.logger.error("post_request_failed",
                            path=path,
                            error=str(e),
                            error_type=type(e).__name__)
            return {"error": f"Failed to process request: {str(e)}"}, 500

    def _calculate_route_cost(self, route_id: str) -> Dict:
        """Calculate costs for a specific route."""
        try:
            # Validate UUID format
            try:
                route_uuid = UUID(route_id)
            except ValueError:
                return {"error": "Invalid route ID format"}, 400

            # Get route from database
            route_model = self.route_repository.get_by_id(route_uuid)
            if not route_model:
                return {"error": "Route not found"}, 404

            # Log the timeline events data
            self.logger.info("route_timeline_events", 
                           route_id=route_id, 
                           timeline_events=route_model.timeline_events)

            # Convert route model to domain entity
            route_dict = route_model.to_dict()
            self.logger.info("route_dict_timeline_events", 
                           route_id=route_id, 
                           timeline_events=route_dict.get('timeline_events'))

            route = Route.from_dict(route_dict)

            # Calculate costs
            self.logger.info("calculating_route_costs", route_id=route_id)
            cost_result = self.cost_calculation_service.calculate_route_cost(route)

            # Update route with new cost data
            route_model.cost_breakdown = cost_result['cost_breakdown']
            route_model.total_cost = cost_result['total_cost']
            route_model.currency = cost_result['currency']
            self.route_repository.update(route_model)

            # Return the cost result directly - no need to jsonify
            return cost_result, 200

        except (RouteValidationError, CostCalculationError) as e:
            self.logger.error("cost_calculation_failed",
                            route_id=route_id,
                            error=str(e),
                            error_type=type(e).__name__)
            return {"error": str(e)}, 400
        except Exception as e:
            self.logger.error("cost_calculation_failed",
                            route_id=route_id,
                            error=str(e),
                            error_type=type(e).__name__)
            return {"error": f"Failed to calculate costs: {str(e)}"}, 500
