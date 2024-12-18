from typing import Optional, List, Dict
from uuid import UUID
import structlog
from datetime import datetime
from sqlalchemy.orm import Session

from .base_repository import BaseRepository
from ..models.route import RouteModel
from ....domain.entities.route import Route, EmptyDriving, MainRoute, CountrySegment
from ....domain.entities.location import Location
from ....domain.entities.cargo import Cargo, TransportType, Capacity
from ....domain.entities.timeline import TimelineEvent

class RouteRepository(BaseRepository):
    """Repository for managing route data in the database."""

    def __init__(self, session: Session):
        """Initialize the repository with a database session."""
        super().__init__(session, RouteModel)
        self.logger = structlog.get_logger(__name__)

    def _to_domain_entity(self, model: RouteModel) -> Route:
        """Convert database model to domain entity."""
        if not model:
            return None

        # Convert Location objects
        origin = Location(
            address=model.origin_address,
            latitude=model.origin_latitude,
            longitude=model.origin_longitude
        )
        destination = Location(
            address=model.destination_address,
            latitude=model.destination_latitude,
            longitude=model.destination_longitude
        )

        # Convert JSON fields to domain objects
        empty_driving_data = model.empty_driving or {}
        empty_driving = EmptyDriving(
            distance_km=empty_driving_data.get('distance_km', 0.0),
            duration_hours=empty_driving_data.get('duration_hours', 0.0),
            country_segments=[
                CountrySegment(**segment)
                for segment in empty_driving_data.get('country_segments', [])
            ],
            base_cost=empty_driving_data.get('base_cost', 0.0)
        )

        main_route_data = model.main_route or {}
        main_route = MainRoute(
            distance_km=main_route_data.get('distance_km', 0.0),
            duration_hours=main_route_data.get('duration_hours', 0.0),
            country_segments=[
                CountrySegment(**segment)
                for segment in main_route_data.get('country_segments', [])
            ],
            base_cost=main_route_data.get('base_cost', 0.0)
        )

        # Convert cargo if present
        cargo_data = model.cargo
        cargo = None
        if cargo_data:
            cargo = Cargo(
                type=cargo_data.get('type'),
                weight=cargo_data.get('weight'),
                value=cargo_data.get('value'),
                special_requirements=cargo_data.get('special_requirements', [])
            )

        # Convert transport type if present
        transport_type_data = model.transport_type
        transport_type = None
        if transport_type_data:
            # Create Capacity first if it exists
            capacity = None
            if transport_type_data.get('capacity'):
                capacity = Capacity(**transport_type_data['capacity'])
            
            transport_type = TransportType(
                name=transport_type_data.get('name') or transport_type_data.get('type', ''),
                capacity=capacity,
                restrictions=transport_type_data.get('restrictions', [])
            )

        # Convert timeline events
        timeline_events = []
        if model.timeline_events:
            for event_data in model.timeline_events:
                # Convert location if present
                location = None
                if event_data.get('location'):
                    location = Location(**event_data.get('location', {}))
                
                # Convert time fields
                event_time = None
                if event_data.get('time'):
                    event_time = datetime.fromisoformat(event_data.get('time'))
                
                # Create TimelineEvent with correct field names
                event = TimelineEvent(
                    type=event_data.get('type', ''),
                    time=event_time,
                    location=location,
                    duration_minutes=event_data.get('duration_minutes', 0),
                    description=event_data.get('description', ''),
                    is_required=event_data.get('is_required', False)
                )
                timeline_events.append(event)

        return Route(
            id=UUID(model.id) if isinstance(model.id, str) else model.id,
            origin=origin,
            destination=destination,
            pickup_time=model.pickup_time,
            delivery_time=model.delivery_time,
            empty_driving=empty_driving,
            main_route=main_route,
            timeline_events=timeline_events,
            total_duration_hours=model.total_duration_hours or 0.0,
            transport_type=transport_type,
            cargo=cargo,
            is_feasible=model.is_feasible
        )

    def get_by_id(self, route_id: UUID) -> Optional[Route]:
        """Get a route by its ID."""
        model = self.session.query(RouteModel).filter(RouteModel.id == str(route_id)).first()
        return self._to_domain_entity(model) if model else None

    def get_all(self) -> List[Route]:
        """Get all routes."""
        models = self.session.query(RouteModel).all()
        return [self._to_domain_entity(model) for model in models]

    def create(self, route: Route) -> RouteModel:
        """Create a new route."""
        try:
            self.logger.debug("Converting route to dictionary")
            route_dict = route.to_dict()
            self.logger.debug("Route dict created", route_dict=route_dict)
            
            # Map the route fields to the model fields
            self.logger.debug("Mapping fields to model")
            model_dict = {
                'id': route_dict.get('id'),  # Keep as UUID
                'origin_address': route_dict.get('origin', {}).get('address'),
                'origin_latitude': float(route_dict.get('origin', {}).get('latitude', 0.0)),
                'origin_longitude': float(route_dict.get('origin', {}).get('longitude', 0.0)),
                'destination_address': route_dict.get('destination', {}).get('address'),
                'destination_latitude': float(route_dict.get('destination', {}).get('latitude', 0.0)),
                'destination_longitude': float(route_dict.get('destination', {}).get('longitude', 0.0)),
                'pickup_time': datetime.fromisoformat(route_dict.get('pickup_time')) if route_dict.get('pickup_time') else None,
                'delivery_time': datetime.fromisoformat(route_dict.get('delivery_time')) if route_dict.get('delivery_time') else None,
                'last_calculated': datetime.fromisoformat(route_dict.get('last_calculated')) if route_dict.get('last_calculated') else None,
                'total_duration_hours': float(route_dict.get('total_duration_hours', 0.0)),
                'total_cost': float(route_dict.get('total_cost', 0.0)),
                'currency': route_dict.get('currency', 'EUR'),
                'is_feasible': bool(route_dict.get('is_feasible', True)),
                'duration_validation': bool(route_dict.get('duration_validation', True))
            }

            # Handle JSON fields separately to ensure proper serialization
            json_fields = [
                'empty_driving', 'main_route', 'timeline', 'timeline_events',
                'transport_type', 'cargo', 'cost_breakdown', 'optimization_insights'
            ]
            for field in json_fields:
                value = route_dict.get(field)
                if value is not None:
                    if isinstance(value, dict):
                        model_dict[field] = value
                    elif hasattr(value, 'to_dict'):
                        model_dict[field] = value.to_dict()
                    elif isinstance(value, list):
                        model_dict[field] = [
                            item.to_dict() if hasattr(item, 'to_dict') else item 
                            for item in value
                        ]
                    else:
                        model_dict[field] = value

            self.logger.debug("Creating route model", model_dict=model_dict)
            route_model = RouteModel(**model_dict)
            self.session.add(route_model)
            self.session.commit()
            self.logger.info("Route saved successfully", route_id=model_dict['id'])
            return route_model

        except Exception as e:
            self.logger.error(
                "Failed to create route",
                error=str(e),
                error_type=type(e).__name__,
                route_id=getattr(route, 'id', None),
                traceback=True
            )
            self.session.rollback()
            raise

    def update(self, route: Route) -> Optional[RouteModel]:
        """Update an existing route."""
        try:
            self.logger.debug("Updating route", route_id=route.id)
            route_model = self.get_by_id(route.id)
            if route_model:
                for key, value in route.to_dict().items():
                    setattr(route_model, key, value)
                self.session.commit()
                self.logger.info("Route updated successfully", route_id=route.id)
            return route_model

        except Exception as e:
            self.logger.error(
                "Failed to update route",
                error=str(e),
                error_type=type(e).__name__,
                route_id=route.id
            )
            raise

    def update_route_costs(self, route_id: UUID, cost_data: Dict) -> Optional[RouteModel]:
        """Update route with calculated costs."""
        try:
            route = self.session.query(RouteModel).filter(RouteModel.id == route_id).first()
            if route:
                route.cost_breakdown = cost_data.get('cost_breakdown', {})
                route.total_cost = cost_data.get('total_cost', 0)
                route.optimization_insights = cost_data.get('optimization_insights', [])
                route.costs_calculated_at = datetime.utcnow()
                self.session.commit()
                return route
            return None
        except Exception as e:
            self.logger.error("failed_to_update_route_costs", 
                            route_id=str(route_id), error=str(e))
            self.session.rollback()
            raise

    def delete(self, route_id: UUID) -> bool:
        """Delete a route by its ID."""
        try:
            self.logger.debug("Deleting route", route_id=route_id)
            route_model = self.get_by_id(route_id)
            if route_model:
                self.session.delete(route_model)
                self.session.commit()
                self.logger.info("Route deleted successfully", route_id=route_id)
                return True
            return False

        except Exception as e:
            self.logger.error(
                "Failed to delete route",
                error=str(e),
                error_type=type(e).__name__,
                route_id=route_id
            )
            raise
