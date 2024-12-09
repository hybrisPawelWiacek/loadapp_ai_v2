from flask import request, current_app, g
from flask_restful import Resource
from datetime import datetime
import structlog
from time import time as get_time

from ...domain.services import RoutePlanningService
from ...domain.entities import Location, Cargo, TransportType, Capacity
from ...infrastructure.database.repository import Repository
from ...infrastructure.database.config import SessionLocal

logger = structlog.get_logger(__name__)

class RouteEndpoint(Resource):
    def __init__(self):
        super().__init__()
        self.route_service = RoutePlanningService()
        self.logger = structlog.get_logger(__name__)
        self.logger.info("route_endpoint_initialized")

    def get_db_session(self):
        """Get a database session for this request."""
        try:
            session = SessionLocal()
            self.logger.info(
                "database_session_created",
                session_type=type(session).__name__
            )
            return session
        except Exception as e:
            self.logger.error(
                "db_session_creation_failed",
                error=str(e),
                error_type=type(e).__name__,
                traceback=True
            )
            return None

    def post(self):
        """Calculate a route."""
        self.logger.debug("Starting post method")
        db = None
        try:
            self.logger.debug("Getting time")
            start_time = get_time()
            self.logger.debug("Got time successfully")

            self.logger.debug("Creating database session")
            # Create database session for this request
            db = self.get_db_session()
            if not db:
                return {"error": "Database connection not available"}, 500
            
            # Create repository
            repository = Repository(db)
            self.logger.info(
                "repository_created",
                repository_type=type(repository).__name__
            )
            
            self.logger.debug("Getting JSON data")
            data = request.get_json()
            if not data:
                self.logger.error("no_request_data")
                return {"error": "No request data provided"}, 400

            self.logger.info("received_route_request", data=data)

            # Parse origin and destination
            self.logger.debug("Parsing locations")
            origin = Location(
                latitude=data["origin"]["latitude"],
                longitude=data["origin"]["longitude"],
                address=data["origin"]["address"]
            )
            destination = Location(
                latitude=data["destination"]["latitude"],
                longitude=data["destination"]["longitude"],
                address=data["destination"]["address"]
            )

            # Parse dates
            self.logger.debug("Parsing dates")
            pickup_time = datetime.fromisoformat(data["pickup_time"].replace('Z', '+00:00'))
            delivery_time = datetime.fromisoformat(data["delivery_time"].replace('Z', '+00:00'))

            # Validate dates
            if delivery_time <= pickup_time:
                return {"error": "Delivery time must be after pickup time"}, 400

            # Parse optional cargo
            self.logger.debug("Parsing cargo")
            cargo = None
            transport_type = None
            if "cargo" in data:
                transport_type = TransportType(
                    name=data['cargo']['type'],
                    capacity=Capacity(),  # Using default capacity
                    restrictions=[]  # No restrictions by default
                )

                cargo = Cargo(
                    type=data['cargo']['type'],
                    weight=float(data['cargo']['weight']),
                    value=float(data['cargo']['value']),
                    special_requirements=data['cargo'].get("special_requirements", [])
                )

            # Calculate route
            self.logger.debug("Calculating route")
            route = self.route_service.calculate_route(
                origin=origin,
                destination=destination,
                pickup_time=pickup_time,
                delivery_time=delivery_time,
                cargo=cargo,
                transport_type=transport_type
            )
            self.logger.info("route_calculated", route_id=str(route.id))

            # Save route to database
            self.logger.debug("Saving route")
            saved_route = repository.save_route(route)
            self.logger.info(
                "route_saved",
                route_id=str(saved_route.id),
                origin=origin.address,
                destination=destination.address
            )

            self.logger.debug("Calculating duration")
            duration = get_time() - start_time
            self.logger.info(
                "metric_recorded",
                metric_name="service_operation_time",
                value=duration,
                labels={
                    "service": "RouteEndpoint",
                    "operation": "post"
                }
            )

            return saved_route.to_dict(), 200

        except KeyError as e:
            self.logger.error("missing_field_error", error=str(e))
            return {"error": f"Missing required field: {str(e)}"}, 400
        except ValueError as e:
            self.logger.error("validation_error", error=str(e))
            return {"error": str(e)}, 400
        except Exception as e:
            self.logger.error(
                "route_calculation_failed",
                error=str(e),
                error_type=type(e).__name__,
                traceback=True
            )
            return {"error": str(e)}, 500
        finally:
            # Clean up database session
            if db:
                try:
                    db.close()
                    self.logger.info("db_session_closed")
                except Exception as e:
                    self.logger.error(
                        "db_session_cleanup_failed",
                        error=str(e),
                        error_type=type(e).__name__
                    )
            self.logger.debug("Calculating final duration")
            duration = get_time() - start_time
            self.logger.info(
                "metric_recorded",
                metric_name="service_operation_time",
                value=duration,
                labels={
                    "service": "RouteEndpoint",
                    "operation": "post"
                }
            )
