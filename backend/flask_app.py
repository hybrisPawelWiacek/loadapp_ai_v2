from flask import Flask, jsonify, request, Blueprint
from flask_restful import Api
from flask_cors import CORS
from uuid import UUID
import structlog
import logging
import time
from datetime import datetime

from backend.api.endpoints.route_endpoint import RouteEndpoint
from backend.api.endpoints.cost_endpoint import CostEndpoint
from backend.api.endpoints.offer_endpoint import OfferEndpoint
from backend.domain.services.cost_calculation_service import CostCalculationService
from backend.domain.services.ai_integration_service import AIIntegrationService
from backend.domain.services.offer_service import OfferService
from backend.domain.services.cost_optimization_service import CostOptimizationService
from backend.infrastructure.database.repositories.cost_setting_repository import CostSettingsRepository
from backend.infrastructure.database.session import SessionLocal, engine, Base
from backend.infrastructure.monitoring.metrics_service import MetricsService
from backend.infrastructure.monitoring.performance_metrics import PerformanceMetrics
from backend.infrastructure.database.db_setup import SQLALCHEMY_DATABASE_URL
from backend.infrastructure.database.init_db import init_db
from backend.infrastructure.database.repositories.base_repository import BaseRepository
from backend.infrastructure.database.repositories.versionable_repository import VersionableRepository
from backend.infrastructure.database.repositories.offer_repository import OfferRepository
from backend.infrastructure.database.models.offer import OfferModel
from backend.infrastructure.database.repositories.route_repository import RouteRepository

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

def create_app():
    """Create and configure the Flask application."""
    logger = structlog.get_logger(__name__)
    logger.info("creating_flask_app")
    
    # Create Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configure CORS for Streamlit frontend
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:8501",
                "http://127.0.0.1:8501"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-API-Key"],
            "expose_headers": ["Content-Type"]
        }
    })
    
    # Add this line after CORS configuration to handle SQLite concurrency
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'connect_args': {'check_same_thread': False}}
    
    # Optional: Global after_request handler for additional CORS headers
    @app.after_request
    def after_request(response):
        origin = request.headers.get('Origin')
        if origin in ["http://localhost:8501", "http://127.0.0.1:8501"]:
            response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization,X-API-Key"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
        return response
    
    api = Api(app)
    
    logger.info("=== STARTING FLASK APP WITH NEW ROUTE CONFIGURATION ===")
    
    # Initialize database first
    try:
        init_db()
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise
        
    # Initialize database session
    session = SessionLocal()
    logger.info("database_session_created", session_type=type(session).__name__)
    
    # Initialize repositories
    cost_settings_repository = CostSettingsRepository(session)
    logger.info("cost_settings_repository_created")
    
    # Initialize monitoring services
    metrics_service = MetricsService()
    logger.info("metrics_service_created")
    
    # Initialize optimization services
    cost_optimization_service = CostOptimizationService(metrics_service=metrics_service)
    logger.info("cost_optimization_service_created")
    
    # Initialize core services
    cost_service = CostCalculationService(
        cost_settings_repository=cost_settings_repository,
        metrics_service=metrics_service,
        cost_optimization_service=cost_optimization_service
    )
    logger.info("cost_service_created")

    ai_service = AIIntegrationService()
    logger.info("ai_service_created")

    # Create a repository for offers
    db_session = SessionLocal()
    offer_repository = OfferRepository(db_session)
    route_repository = RouteRepository(db_session)

    offer_service = OfferService(
        db_repository=offer_repository,
        cost_service=cost_service,
        route_repository=route_repository,
        ai_service=ai_service
    )
    logger.info("offer_service_created")

    # Test route to verify code changes
    @app.route('/test_route')
    def test_route():
        return jsonify({"message": "Test route working!"})
    
    # Initialize endpoints with their required services
    route_endpoint = RouteEndpoint(
        repository=None,  # Will be created per request
        metrics_service=metrics_service,
        cost_settings_repository=cost_settings_repository,
        cost_calculation_service=cost_service
    )
    cost_endpoint = CostEndpoint(
        repository=None,  # Will be created per request
        metrics_service=metrics_service,
        cost_settings_repository=cost_settings_repository,
        cost_calculation_service=cost_service,
        cost_optimization_service=cost_optimization_service
    )
    offer_endpoint = OfferEndpoint(
        offer_service=offer_service
    )

    # Register API endpoints
    api_bp = Blueprint('api', __name__, url_prefix='/api/v1')
    api = Api(api_bp)

    # Register cost endpoint
    api.add_resource(
        CostEndpoint, 
        '/costs',
        '/costs/<string:cost_id>',
        '/costs/settings',
        resource_class_kwargs={
            'repository': None,  # Will be created per request
            'metrics_service': metrics_service,
            'cost_settings_repository': cost_settings_repository,
            'cost_calculation_service': cost_service,
            'cost_optimization_service': cost_optimization_service
        }
    )

    # Register route endpoint
    api.add_resource(
        RouteEndpoint, 
        '/routes',
        '/routes/<string:route_id>',
        resource_class_kwargs={
            'repository': None,  # Will be created per request
            'metrics_service': metrics_service,
            'cost_settings_repository': cost_settings_repository,
            'cost_calculation_service': cost_service,
            'cost_optimization_service': cost_optimization_service
        }
    )

    # Register offer endpoint
    api.add_resource(
        OfferEndpoint,
        '/offers',
        '/offers/<string:offer_id>',
        resource_class_kwargs={
            'offer_service': offer_service
        }
    )

    # Register the blueprint with the app
    app.register_blueprint(api_bp)

    logger.info("api_routes_registered", 
        endpoints=[
            "/api/v1/costs/settings",
            "/api/v1/costs/<cost_id>",
            "/api/v1/routes",
            "/api/v1/routes/<route_id>",
            "/api/v1/offers",
            "/api/v1/offers/<offer_id>"
        ]
    )

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
        """Handle any uncaught exceptions with detailed logging."""
        logger.error(
            "unhandled_error",
            error=str(error),
            error_type=type(error).__name__,
            error_details=getattr(error, 'errors', None),
            traceback=True
        )
        return {
            "error": "Failed to calculate route. Please try again.",
            "details": str(error),
            "type": type(error).__name__
        }, 500

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
    import asyncio
    from threading import Thread
    
    # Create a new event loop for the background thread
    background_loop = asyncio.new_event_loop()
    
    def run_background_loop(loop):
        """Run the event loop in the background."""
        asyncio.set_event_loop(loop)
        loop.run_forever()
    
    # Start background thread for asyncio
    background_thread = Thread(target=run_background_loop, args=(background_loop,), daemon=True)
    background_thread.start()
    
    try:
        app.run(debug=True, port=5001)
    finally:
        # Cleanup
        background_loop.call_soon_threadsafe(background_loop.stop)
        background_thread.join(timeout=1.0)
        background_loop.close()
