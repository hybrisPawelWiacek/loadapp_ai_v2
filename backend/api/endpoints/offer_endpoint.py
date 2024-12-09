from flask import request, jsonify
from flask_restful import Resource, reqparse
import structlog
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid
from uuid import UUID, uuid4
import traceback
import json

from ...domain.services.offer_service import OfferService
from ...domain.services.cost_calculation_service import CostCalculationService
from ...domain.services.cost_optimization_service import CostOptimizationService
from ...domain.services.ai_integration_service import AIIntegrationService
from ...infrastructure.database.repositories.offer_repository import OfferRepository
from ...infrastructure.database.repositories.cost_setting_repository import CostSettingsRepository
from ...infrastructure.database.repositories.route_repository import RouteRepository
from ...infrastructure.database.session import SessionLocal
from ...infrastructure.database.models.offer import OfferModel
from ...infrastructure.monitoring.metrics_service import MetricsService
from ...domain.entities.offer import OfferStatus
from ...domain.exceptions import ValidationError, BusinessRuleError, ResourceNotFoundError

logger = structlog.get_logger(__name__)

class OfferEndpoint(Resource):
    def __init__(self, repository: Optional[OfferRepository] = None,
                 metrics_service: Optional[MetricsService] = None,
                 cost_settings_repository: Optional[CostSettingsRepository] = None,
                 route_repository: Optional[RouteRepository] = None,
                 cost_calculation_service: Optional[CostCalculationService] = None,
                 cost_optimization_service: Optional[CostOptimizationService] = None,
                 offer_service: Optional[OfferService] = None):
        """Initialize the OfferEndpoint with optional dependencies."""
        super().__init__()
        
        # Initialize logger first
        self.logger = logger.bind(
            endpoint="offer_endpoint",
            method=request.method if request else None
        )
        self.logger.info("offer_endpoint_initialized")
        
        # Create a new database session
        db_session = SessionLocal()
        
        # Initialize repositories
        if repository is None:
            self.repository = OfferRepository(db_session)
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
        
        # Initialize cost optimization service
        if cost_optimization_service is None:
            self.cost_optimization_service = CostOptimizationService(
                metrics_service=self.metrics_service
            )
        else:
            self.cost_optimization_service = cost_optimization_service
        
        # Initialize cost calculation service
        if cost_calculation_service is None:
            self.logger.info("creating_cost_calculation_service")
            self.cost_calculation_service = CostCalculationService(
                cost_settings_repository=self.cost_settings_repository,
                metrics_service=self.metrics_service,
                cost_optimization_service=self.cost_optimization_service
            )
        else:
            self.cost_calculation_service = cost_calculation_service
        
        # Initialize AI service
        self.ai_service = AIIntegrationService()
        
        # Initialize offer service with all required dependencies
        if offer_service is None:
            self.logger.info(
                "creating_offer_service",
                cost_service_type=type(self.cost_calculation_service).__name__,
                ai_service_type=type(self.ai_service).__name__
            )
            self.offer_service = OfferService(
                db_repository=self.repository,
                cost_service=self.cost_calculation_service,  # Pass the properly initialized cost service
                ai_service=self.ai_service
            )
        else:
            self.offer_service = offer_service
        
        # Initialize request parser for common parameters
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('page', type=int, location='args')
        self.parser.add_argument('per_page', type=int, location='args')
        self.parser.add_argument('sort_by', type=str, location='args')
        self.parser.add_argument('sort_order', type=str, location='args')
        self.parser.add_argument('filter_by', type=str, location='args')
        self.parser.add_argument('filter_value', type=str, location='args')
        self.parser.add_argument('include_deleted', type=str, location='args')
        self.parser.add_argument('include_history', type=str, location='args')
        self.parser.add_argument('include_metrics', type=str, location='args')

    def _log_request_params(self, method: str, **params) -> None:
        """Log request parameters with method, timestamp, and client info."""
        self.logger.info(
            "offer_endpoint_request",
            method=method,
            timestamp=datetime.utcnow().isoformat(),
            client_ip=request.remote_addr,
            user_agent=request.user_agent.string,
            endpoint=request.endpoint,
            path=request.path,
            **params
        )

    def _handle_error(self, error: Exception, context: Dict[str, Any]) -> Tuple[Dict[str, str], int]:
        """Handle different types of errors with appropriate logging and responses."""
        error_id = str(uuid4())
        error_details = {
            'error_id': error_id,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc()
        }
        
        if isinstance(error, ValidationError):
            self.logger.warning(
                "offer_validation_error",
                **context,
                **error_details
            )
            return {"error": "Validation error", "details": str(error)}, 400
            
        elif isinstance(error, BusinessRuleError):
            self.logger.warning(
                "offer_business_rule_error",
                **context,
                **error_details
            )
            return {"error": "Business rule violation", "details": str(error)}, 422
            
        elif isinstance(error, ResourceNotFoundError):
            self.logger.info(
                "offer_not_found",
                **context,
                **error_details
            )
            return {"error": "Resource not found", "details": str(error)}, 404
            
        else:
            self.logger.error(
                "offer_unhandled_error",
                **context,
                **error_details
            )
            return {
                "error": "Internal server error",
                "error_id": error_id,
                "message": "An unexpected error occurred. Please contact support with this error ID."
            }, 500

    def get(self, offer_id: Optional[str] = None) -> Tuple[Dict[str, Any], int]:
        """
        Handle GET requests for offers.
        
        Endpoints:
        - GET /api/v1/offers/<offer_id>: Get specific offer
        - GET /api/v1/offers: Get filtered list of offers
        """
        context = {"offer_id": offer_id} if offer_id else {}
        
        try:
            # Log request parameters
            if offer_id:
                self._log_request_params("GET", offer_id=offer_id)
            else:
                args = self.parser.parse_args()
                self._log_request_params("GET", **{k: v for k, v in args.items() if v is not None})
                context.update(args)
            
            if offer_id:
                # Get specific offer
                try:
                    uuid_id = UUID(offer_id)
                except ValueError as e:
                    self.logger.warning(
                        "invalid_offer_id_format",
                        offer_id=offer_id,
                        error=str(e)
                    )
                    return {"error": "Invalid offer ID format"}, 400
                    
                offer = self.offer_service.get_offer(uuid_id)
                if not offer:
                    self.logger.info("offer_not_found", offer_id=offer_id)
                    return {"error": "Offer not found"}, 404
                
                self.logger.info("offer_retrieved", offer_id=offer_id)
                return offer.to_dict(), 200
            
            # Get filtered list of offers
            try:
                args = self.parser.parse_args()
                
                # Parse query parameters with proper validation
                filters = {
                    'start_date': datetime.fromisoformat(args['start_date']) if args['start_date'] else None,
                    'end_date': datetime.fromisoformat(args['end_date']) if args['end_date'] else None,
                    'min_price': float(args['min_price'] or 0),
                    'max_price': float(args['max_price'] or float('inf')),
                    'status': args['status'],
                    'currency': args['currency'],
                    'countries': json.loads(args['countries']) if args['countries'] else None,
                    'regions': json.loads(args['regions']) if args['regions'] else None,
                    'client_id': UUID(args['client_id']) if args['client_id'] else None
                }
                
                # Parse pagination parameters
                page = args['page']
                page_size = args['page_size']
                
                # Parse include flags
                include_settings = args['include_settings'].lower() == 'true' if args['include_settings'] else False
                include_history = args['include_history'].lower() == 'true' if args['include_history'] else False
                include_metrics = args['include_metrics'].lower() == 'true' if args['include_metrics'] else False
                
                # Validate pagination parameters
                if page < 1:
                    return {"error": "Page number must be greater than 0"}, 400
                if page_size < 1 or page_size > 100:
                    return {"error": "Page size must be between 1 and 100"}, 400
                
                # Get offers with filters
                offers = self.offer_service.list_offers_with_filters(
                    **filters,
                    offset=(page - 1) * page_size,
                    limit=page_size,
                    include_settings=include_settings,
                    include_history=include_history,
                    include_metrics=include_metrics
                )
                
                # Get total count for pagination
                total_count = self.offer_service.count_offers_with_filters(**filters)
                
                # Transform offers for response
                response_data = {
                    "offers": [offer.to_dict() for offer in offers],
                    "total": total_count,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total_count + page_size - 1) // page_size
                }
                
                self.logger.info(
                    "offers_listed",
                    total_offers=len(offers),
                    total_count=total_count,
                    page=page,
                    page_size=page_size,
                    **context
                )
                return response_data, 200

            except ValueError as e:
                self.logger.warning(
                    "invalid_parameter_format",
                    error=str(e),
                    **context
                )
                return {"error": "Invalid parameter format", "details": str(e)}, 400

        except Exception as e:
            return self._handle_error(e, context)

    def post(self) -> Tuple[Dict[str, Any], int]:
        """
        Create a new offer.
        
        Endpoint: POST /api/v1/offers
        """
        try:
            self.logger.info("offer_endpoint_post_called")
            
            data = request.get_json()
            if not data:
                return {"error": "No JSON data provided"}, 400
                
            required_fields = ['route_id']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return {"error": f"Missing required fields: {', '.join(missing_fields)}"}, 400

            try:
                route_id = UUID(data['route_id'])
            except ValueError:
                return {"error": "Invalid route ID format"}, 400

            # Fetch the route first
            route = self.route_repository.get_by_id(route_id)
            if not route:
                return {"error": "Route not found"}, 404

            # Create the offer
            offer = self.offer_service.generate_offer(
                route=route,
                cost_settings={},  # TODO: Get from settings service
                margin_percentage=data.get('margin', 10.0),
                currency=data.get('currency', 'EUR'),
                client_id=UUID(data['client_id']) if data.get('client_id') else None,
                client_name=data.get('client_name'),
                client_contact=data.get('client_contact'),
                geographic_restrictions=data.get('geographic_restrictions')
            )

            response = offer.to_dict()
            self.logger.info("offer_created", offer_id=str(offer.id))
            return response, 201

        except Exception as e:
            return self._handle_error(e, {})

    def put(self, offer_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Update an existing offer.
        
        Endpoint: PUT /api/v1/offers/<offer_id>
        """
        try:
            self.logger.info("offer_endpoint_put_called", offer_id=offer_id)
            
            try:
                uuid_id = UUID(offer_id)
            except ValueError:
                return {"error": "Invalid offer ID format"}, 400

            data = request.get_json()
            if not data:
                return {"error": "No JSON data provided"}, 400

            # Handle status transition
            if 'status' in data and len(data) == 1:
                success = self.offer_service.transition_status(uuid_id, data['status'])
                if not success:
                    return {"error": "Invalid status transition"}, 400
                return {"message": "Status updated successfully"}, 200

            # Handle full update
            updated_offer = self.offer_service.update_offer(
                offer_id=uuid_id,
                update_data=data,
                user_id=request.headers.get('X-User-ID', 'system')
            )
            
            if not updated_offer:
                return {"error": "Offer not found"}, 404

            self.logger.info("offer_updated", offer_id=offer_id)
            return updated_offer.to_dict(), 200

        except Exception as e:
            return self._handle_error(e, {"offer_id": offer_id})

    def delete(self, offer_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Delete an offer (soft delete).
        
        Endpoint: DELETE /api/v1/offers/<offer_id>
        """
        try:
            self.logger.info("offer_endpoint_delete_called", offer_id=offer_id)
            
            try:
                uuid_id = UUID(offer_id)
            except ValueError:
                return {"error": "Invalid offer ID format"}, 400

            success = self.offer_service.delete_offer(
                offer_id=uuid_id,
                user_id=request.headers.get('X-User-ID', 'system'),
                reason=request.args.get('reason', 'User requested deletion')
            )
            
            if not success:
                return {"error": "Offer not found"}, 404

            self.logger.info("offer_deleted", offer_id=offer_id)
            return {"message": "Offer deleted successfully"}, 200

        except Exception as e:
            return self._handle_error(e, {"offer_id": offer_id})
