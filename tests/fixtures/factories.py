import factory
from factory.fuzzy import FuzzyFloat, FuzzyText, FuzzyChoice
from datetime import datetime, timedelta
from typing import Dict, Any

from backend.domain.entities.route import Route, RouteStatus
from backend.domain.entities.offer import Offer, OfferStatus
from backend.domain.entities.cost import Cost
from backend.domain.entities.location import Location
from backend.domain.entities.user import User
from backend.domain.entities.cargo import TransportType as Vehicle

class LocationFactory(factory.Factory):
    class Meta:
        model = Location

    latitude = FuzzyFloat(low=-90, high=90)
    longitude = FuzzyFloat(low=-180, high=180)
    address = FuzzyText(prefix='Address-', length=50)
    city = factory.Faker('city')
    country = factory.Faker('country')
    postal_code = factory.Faker('postcode')

class VehicleFactory(factory.Factory):
    class Meta:
        model = Vehicle

    type = FuzzyChoice(['TRUCK', 'VAN', 'CARGO'])
    capacity = FuzzyFloat(low=1000, high=10000)  # in kg
    dimensions = factory.LazyFunction(
        lambda: {'length': 500, 'width': 200, 'height': 200}  # in cm
    )
    features = factory.LazyFunction(
        lambda: ['GPS', 'REFRIGERATION', 'TAIL_LIFT']
    )

class RouteFactory(factory.Factory):
    class Meta:
        model = Route

    origin = factory.SubFactory(LocationFactory)
    destination = factory.SubFactory(LocationFactory)
    pickup_time = factory.Faker('future_datetime')
    delivery_time = factory.LazyAttribute(
        lambda o: o.pickup_time + timedelta(hours=factory.Faker('random_int', min=1, max=48))
    )
    status = FuzzyChoice([status for status in RouteStatus])
    distance = FuzzyFloat(low=10, high=1000)  # in km
    duration = FuzzyFloat(low=0.5, high=48)   # in hours
    vehicle_requirements = factory.SubFactory(VehicleFactory)

    @factory.post_generation
    def calculate_metrics(obj, create, extracted, **kwargs):
        """Calculate route metrics after creation."""
        if not create:
            return
        
        # Calculate additional metrics
        obj.total_distance = obj.distance * 1.1  # Add 10% buffer
        obj.estimated_duration = obj.duration * 1.2  # Add 20% buffer

class CostFactory(factory.Factory):
    class Meta:
        model = Cost

    base_rate = FuzzyFloat(low=100, high=500)
    distance_rate = FuzzyFloat(low=1, high=5)
    time_rate = FuzzyFloat(low=20, high=100)
    vehicle_rate = FuzzyFloat(low=50, high=200)
    special_requirements_rate = FuzzyFloat(low=0, high=100)
    
    @factory.post_generation
    def calculate_total(obj, create, extracted, **kwargs):
        """Calculate total cost after creation."""
        if not create:
            return
        
        obj.total = (
            obj.base_rate +
            obj.distance_rate +
            obj.time_rate +
            obj.vehicle_rate +
            obj.special_requirements_rate
        )

class OfferFactory(factory.Factory):
    class Meta:
        model = Offer

    route = factory.SubFactory(RouteFactory)
    cost = factory.SubFactory(CostFactory)
    status = FuzzyChoice([status for status in OfferStatus])
    margin_percentage = FuzzyFloat(low=10, high=30)
    valid_until = factory.Faker('future_datetime')
    
    @factory.post_generation
    def calculate_final_price(obj, create, extracted, **kwargs):
        """Calculate final price after creation."""
        if not create:
            return
        
        obj.final_price = obj.cost.total * (1 + obj.margin_percentage / 100)

class UserFactory(factory.Factory):
    class Meta:
        model = User

    email = factory.Faker('email')
    username = factory.Faker('user_name')
    full_name = factory.Faker('name')
    company = factory.Faker('company')
    role = FuzzyChoice(['ADMIN', 'USER', 'MANAGER'])
    preferences = factory.LazyFunction(
        lambda: {
            'notifications': True,
            'language': 'en',
            'timezone': 'UTC'
        }
    )

# Batch creation helpers
def create_route_with_offers(
    num_offers: int = 3,
    route_params: Dict[str, Any] = None,
    offer_params: Dict[str, Any] = None
) -> tuple[Route, list[Offer]]:
    """Create a route with multiple offers."""
    route = RouteFactory.create(**(route_params or {}))
    offers = [
        OfferFactory.create(route=route, **(offer_params or {}))
        for _ in range(num_offers)
    ]
    return route, offers

def create_user_with_routes(
    num_routes: int = 5,
    user_params: Dict[str, Any] = None,
    route_params: Dict[str, Any] = None
) -> tuple[User, list[Route]]:
    """Create a user with multiple routes."""
    user = UserFactory.create(**(user_params or {}))
    routes = [
        RouteFactory.create(**(route_params or {}))
        for _ in range(num_routes)
    ]
    return user, routes

def create_complex_scenario(
    num_users: int = 3,
    routes_per_user: int = 2,
    offers_per_route: int = 3
) -> Dict[str, Any]:
    """Create a complex test scenario with multiple users, routes, and offers."""
    scenario = {
        'users': [],
        'routes': [],
        'offers': []
    }

    for _ in range(num_users):
        user = UserFactory.create()
        scenario['users'].append(user)
        
        for _ in range(routes_per_user):
            route = RouteFactory.create()
            scenario['routes'].append(route)
            
            offers = [
                OfferFactory.create(route=route)
                for _ in range(offers_per_route)
            ]
            scenario['offers'].extend(offers)

    return scenario 