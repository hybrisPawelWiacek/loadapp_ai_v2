from flask import Flask, jsonify, request, Blueprint
from flask_restful import Api
from flask_cors import CORS
from uuid import UUID
import structlog
import logging
import time

from backend.api.endpoints import RouteEndpoint, CostEndpoint
from backend.domain.services.cost_calculation_service import CostCalculationService
from backend.domain.services.ai_integration_service import AIIntegrationService
from backend.domain.services.offer_service import OfferService
from backend.infrastructure.database.repository import Repository
from backend.infrastructure.monitoring.performance_metrics import PerformanceMetrics
from backend.infrastructure.database.db_setup import SessionLocal, engine, Base, SQLALCHEMY_DATABASE_URL
from backend.infrastructure.database.init_db import init_db

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Configure structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False
)

logger = structlog.get_logger(__name__)

def create_app():
    """Create and configure the Flask application."""
    logger.info("creating_flask_app")
    
    # Initialize Flask app
    app = Flask(__name__)
    app.debug = True  # Enable debug mode
    
    # Basic configuration
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE='loadapp.db',
        SQLALCHEMY_DATABASE_URI=SQLALCHEMY_DATABASE_URL,
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    
    # Initialize API
    api = Api(app)
    
    # Enable CORS
    CORS(app)
    
    logger.info("=== STARTING FLASK APP WITH NEW ROUTE CONFIGURATION ===")
    
    # Test route to verify code changes
    @app.route('/test_route')
    def test_route():
        return jsonify({"message": "Test route working!"})
    
    # Initialize database
    logger.info("initializing_database")
    init_db()  # This will create tables and add default cost settings
    logger.info("database_initialized")
    
    # Initialize database session
    session = SessionLocal()
    logger.info("database_session_created", session_type=type(session).__name__)
    
    # Initialize repository with session
    repository = Repository(session)
    logger.info("repository_created", repository_type=type(repository).__name__)
    
    # Initialize services
    cost_service = CostCalculationService()
    logger.info("cost_service_created")

    # Initialize AI service
    ai_service = AIIntegrationService()
    logger.info("ai_service_created")

    # Initialize offer service
    offer_service = OfferService(cost_service, ai_service, repository)
    logger.info("offer_service_created")

    # Initialize metrics
    app.metrics = PerformanceMetrics()
    
    # Register route endpoint with Flask-RESTful
    api.add_resource(RouteEndpoint, '/route', methods=['GET', 'POST'])

    @app.route('/costs/<route_id>', methods=['POST'])
    def calculate_costs(route_id):
        """Direct route handler for cost calculation."""
        logger.info("cost_calculation_request_received", route_id=route_id)
        
        try:
            # Parse route ID
            try:
                route_uuid = UUID(str(route_id))
                logger.info("route_id_parsed", route_id=route_id)
            except ValueError:
                logger.error("invalid_route_id_format", route_id=route_id)
                return jsonify({"error": f"Invalid route ID format: {route_id}"}), 400

            # Get route from database
            route = repository.get_route(route_uuid)
            if not route:
                logger.error("route_not_found", route_id=route_id)
                return jsonify({"error": f"Route not found: {route_id}"}), 404

            logger.info("route_found", route_id=route_id)

            # Calculate costs
            costs = cost_service.calculate_total_cost(route)
            
            logger.info("costs_calculated", route_id=route_id, costs=costs)
            return jsonify(costs)

        except Exception as e:
            logger.error("cost_calculation_error", error=str(e), route_id=route_id)
            return jsonify({"error": str(e)}), 500

    @app.route('/offer', methods=['POST'])
    def generate_offer():
        """Generate an offer for a route."""
        logger.info("offer_generation_request_received")
        
        try:
            data = request.get_json()
            if not data or 'route_id' not in data:
                logger.error("missing_route_id")
                return jsonify({"error": "Missing route_id in request"}), 400

            # Get route from database
            route = repository.get_route(UUID(data['route_id']))
            if not route:
                logger.error("route_not_found", route_id=data['route_id'])
                return jsonify({"error": f"Route not found: {data['route_id']}"}), 404

            # Generate offer
            margin = data.get('margin', 20.0)  # Default 20% margin if not specified
            offer = offer_service.generate_offer(route, margin=margin)
            
            logger.info("offer_generated", 
                       offer_id=str(offer.id), 
                       route_id=str(route.id),
                       margin=margin)
            
            return jsonify(offer.to_dict()), 201

        except ValueError as e:
            logger.error("invalid_data_format", error=str(e))
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error("offer_generation_failed", error=str(e))
            return jsonify({"error": str(e)}), 500

    # Create cost endpoint instance
    cost_endpoint = CostEndpoint()

    # Register cost endpoints using Blueprint
    costs_bp = Blueprint('costs', __name__)

    @costs_bp.route('/settings', methods=['GET', 'POST'])
    def handle_cost_settings():
        logger.info("handling_cost_settings", method=request.method)
        if request.method == 'GET':
            return cost_endpoint.get()
        else:
            return cost_endpoint.post()

    @costs_bp.route('/<route_id>', methods=['GET', 'POST'])
    def handle_route_costs(route_id):
        logger.info("handling_route_costs", 
                   route_id=route_id, 
                   method=request.method, 
                   path=request.path,
                   full_url=request.url)
        try:
            if request.method == 'GET':
                return cost_endpoint.get(route_id)
            else:
                return cost_endpoint.post(route_id)
        except Exception as e:
            logger.error("route_costs_handler_error", 
                        error=str(e),
                        route_id=route_id,
                        method=request.method)
            return {"error": str(e)}, 500

    # Register the blueprint with a URL prefix
    app.register_blueprint(costs_bp, url_prefix='/costs')
    
    # Log all registered routes
    logger.info("=== REGISTERED ROUTES ===")
    for rule in app.url_map.iter_rules():
        logger.info("route_registered", path=str(rule), methods=list(rule.methods))

    @app.before_request
    def before_request():
        """Set up request context."""
        request.start_time = time.time()
        logger.info(
            "request_started",
            path=request.path,
            method=request.method,
            endpoint=request.endpoint,
            url_rule=str(request.url_rule) if request.url_rule else None,
            args=dict(request.args),
            remote_addr=request.remote_addr
        )

    @app.after_request
    def after_request(response):
        """Log response info and record timing metrics."""
        try:
            if hasattr(request, 'start_time'):
                duration = time.time() - request.start_time
                logger.info(
                    "request_completed",
                    path=request.path,
                    method=request.method,
                    status=response.status_code,
                    duration=duration
                )
        except Exception as e:
            logger.error("after_request_handler_failed", error=str(e))
        return response

    @app.errorhandler(404)
    def handle_404(error):
        """Handle 404 errors with detailed logging."""
        logger.error(
            "route_not_found",
            path=request.path,
            method=request.method,
            endpoint=request.endpoint,
            url_rule=str(request.url_rule) if request.url_rule else None,
            error=str(error)
        )
        return jsonify({
            "error": "Not Found",
            "message": str(error),
            "path": request.path,
            "method": request.method
        }), 404

    @app.errorhandler(Exception)
    def handle_error(error):
        """Handle any uncaught exceptions."""
        logger.error(
            "unhandled_error", 
            error=str(error), 
            type=type(error).__name__,
            path=request.path,
            method=request.method,
            endpoint=request.endpoint,
            url_rule=str(request.url_rule) if request.url_rule else None
        )
        return jsonify({
            "error": str(error),
            "type": type(error).__name__
        }), 500

    logger.info(
        "flask_app_created",
        has_session=hasattr(app, 'Session'),
        has_route_service=hasattr(app, 'route_service'),
        has_cost_service=hasattr(app, 'cost_service'),
        has_offer_service=hasattr(app, 'offer_service')
    )
    return app

# Create and initialize the Flask application
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
