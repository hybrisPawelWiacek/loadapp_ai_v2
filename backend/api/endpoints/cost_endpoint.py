from flask import request, jsonify
from flask_restful import Resource
from uuid import UUID
import structlog

from ...domain.services import CostCalculationService
from ...infrastructure.database import Repository, get_db_session
from ...domain.entities import Route, Cost

class CostEndpoint(Resource):
    def __init__(self):
        self.cost_service = CostCalculationService()
        self.repository = Repository(get_db_session())
        self.logger = structlog.get_logger(__name__)
        self.logger.info("cost_endpoint_initialized")

    def get(self, route_id=None):
        """Get cost settings or calculate costs for a specific route."""
        self.logger.info("cost_endpoint_get_called", route_id=route_id)
        
        try:
            if route_id is None or route_id == 'settings':
                # Return cost settings
                self.logger.info("returning_cost_settings")
                settings = self.repository.get_cost_settings()
                return jsonify([setting.to_dict() for setting in settings])
            
            # Get route from database
            try:
                route_uuid = UUID(str(route_id))
                self.logger.info("parsed_route_id", route_id=route_id, uuid=str(route_uuid))
            except ValueError as e:
                self.logger.error("invalid_route_id_format", route_id=route_id, error=str(e))
                return {"error": f"Invalid route ID format: {route_id}"}, 400

            route = self.repository.get_route(route_uuid)
            if not route:
                self.logger.error("route_not_found", route_id=route_id)
                return {"error": f"Route with ID {route_id} not found"}, 404

            self.logger.info("route_found", 
                           route_id=route_id,
                           has_empty_driving=bool(route.empty_driving),
                           has_main_route=bool(route.main_route))

            # Calculate costs
            costs = self.cost_service.calculate_total_cost(route)
            self.logger.info("costs_calculated", 
                           route_id=route_id,
                           total_cost=costs.total_cost)
            
            return jsonify(costs.to_dict())
            
        except Exception as e:
            self.logger.error("cost_calculation_failed", 
                            error=str(e),
                            error_type=type(e).__name__,
                            route_id=route_id)
            return {"error": str(e)}, 500

    def post(self, route_id=None):
        """Update cost settings or trigger cost calculation for a route."""
        self.logger.info("cost_endpoint_post_called", route_id=route_id)
        
        try:
            if route_id is None or route_id == 'settings':
                # Create new cost setting
                data = request.get_json()
                setting = self.repository.create_cost_setting(
                    country=data["country"],
                    cargo_type=data["cargo_type"],
                    base_rate=data["base_rate"],
                    distance_rate=data["distance_rate"],
                    time_rate=data["time_rate"]
                )
                self.logger.info("cost_setting_created", setting_id=setting.id)
                return setting.to_dict(), 201
            
            # Get route from database
            try:
                route_uuid = UUID(str(route_id))
                self.logger.info("parsed_route_id", route_id=route_id, uuid=str(route_uuid))
            except ValueError as e:
                self.logger.error("invalid_route_id_format", route_id=route_id, error=str(e))
                return {"error": f"Invalid route ID format: {route_id}"}, 400

            route = self.repository.get_route(route_uuid)
            if not route:
                self.logger.error("route_not_found", route_id=route_id)
                return {"error": f"Route with ID {route_id} not found"}, 404

            self.logger.info("route_found", 
                           route_id=route_id,
                           has_empty_driving=bool(route.empty_driving),
                           has_main_route=bool(route.main_route))

            # Calculate costs with any additional parameters from the request
            params = request.get_json() or {}
            costs = self.cost_service.calculate_total_cost(route)
            self.logger.info("costs_calculated", 
                           route_id=route_id,
                           total_cost=costs.total_cost,
                           params=params)
            
            return jsonify(costs.to_dict())
            
        except Exception as e:
            self.logger.error("cost_calculation_failed", 
                            error=str(e),
                            error_type=type(e).__name__,
                            route_id=route_id)
            return {"error": str(e)}, 500

    def put(self):
        """Update cost settings."""
        try:
            data = request.get_json()
            setting = self.repository.update_cost_setting(
                id=data["id"],
                type=data.get("type"),
                category=data.get("category"),
                base_value=data.get("base_value"),
                multiplier=data.get("multiplier"),
                currency=data.get("currency"),
                is_enabled=data.get("is_enabled"),
                description=data.get("description")
            )
            self.logger.info("cost_setting_updated", setting_id=setting.id)
            return setting.to_dict(), 200
        except KeyError as e:
            self.logger.error("missing_required_field", error=str(e))
            return {"error": f"Missing required field: {str(e)}"}, 400
        except Exception as e:
            self.logger.error("put_costs_failed", error=str(e), error_type=type(e).__name__)
            return {"error": str(e)}, 500
