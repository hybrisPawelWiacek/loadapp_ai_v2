import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import inspect, text
from backend.infrastructure.database.db_setup import get_db, engine, Base
from backend.infrastructure.database.models import Route, Offer, CostItem
from backend.infrastructure.database.repository import Repository

@pytest.fixture(scope="function")
def db_session():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Get a test database session
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()
        # Clean up after test
        Base.metadata.drop_all(bind=engine)

def test_database_tables_exist(db_session):
    """Test that all required tables are created in the database with correct columns"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    # Check required tables exist
    required_tables = [
        'routes', 'offers', 'cost_items', 
        'metric_logs', 'metric_aggregates', 
        'alert_rules', 'alert_events'
    ]
    for table in required_tables:
        assert table in tables, f"Table {table} not found in database"
    
    # Check routes table columns
    route_columns = {col['name'] for col in inspector.get_columns('routes')}
    required_route_columns = {
        'id', 'origin_latitude', 'origin_longitude', 'origin_address',
        'destination_latitude', 'destination_longitude', 'destination_address',
        'pickup_time', 'delivery_time', 'total_duration_hours', 'total_cost',
        'is_feasible', 'duration_validation', 'transport_type', 'cargo',
        'currency', 'created_at', 'empty_driving', 'main_route', 'timeline'
    }
    assert required_route_columns.issubset(route_columns), "Missing required columns in routes table"
    
    # Check offers table columns
    offer_columns = {col['name'] for col in inspector.get_columns('offers')}
    required_offer_columns = {
        'id', 'route_id', 'total_cost', 'margin', 'final_price',
        'fun_fact', 'status', 'cost_breakdown', 'created_at'
    }
    assert required_offer_columns.issubset(offer_columns), "Missing required columns in offers table"
    
    # Check cost_items table columns
    cost_columns = {col['name'] for col in inspector.get_columns('cost_items')}
    required_cost_columns = {
        'id', 'type', 'category', 'base_value', 'multiplier', 'currency',
        'is_enabled', 'description', 'created_at', 'updated_at'
    }
    assert required_cost_columns.issubset(cost_columns), "Missing required columns in cost_items table"

    # Check metric_logs table columns
    metric_log_columns = {col['name'] for col in inspector.get_columns('metric_logs')}
    required_metric_log_columns = {
        'id', 'name', 'value', 'labels', 'timestamp'
    }
    assert required_metric_log_columns.issubset(metric_log_columns), "Missing required columns in metric_logs table"

    # Check metric_aggregates table columns
    metric_agg_columns = {col['name'] for col in inspector.get_columns('metric_aggregates')}
    required_metric_agg_columns = {
        'id', 'name', 'period', 'start_time', 'end_time', 'count',
        'sum', 'avg', 'min', 'max', 'p95', 'labels'
    }
    assert required_metric_agg_columns.issubset(metric_agg_columns), "Missing required columns in metric_aggregates table"

    # Check alert_rules table columns
    alert_rule_columns = {col['name'] for col in inspector.get_columns('alert_rules')}
    required_alert_rule_columns = {
        'id', 'name', 'metric_name', 'condition', 'threshold', 'period',
        'labels_filter', 'enabled', 'created_at'
    }
    assert required_alert_rule_columns.issubset(alert_rule_columns), "Missing required columns in alert_rules table"

    # Check alert_events table columns
    alert_event_columns = {col['name'] for col in inspector.get_columns('alert_events')}
    required_alert_event_columns = {
        'id', 'rule_id', 'triggered_at', 'value', 'message', 'resolved_at'
    }
    assert required_alert_event_columns.issubset(alert_event_columns), "Missing required columns in alert_events table"

def test_route_crud_operations(db_session):
    """Test Create, Read, Update, Delete operations for Route"""
    # Create test route
    route_data = {
        "origin_latitude": 52.5200,
        "origin_longitude": 13.4050,
        "origin_address": "Berlin, Germany",
        "destination_latitude": 48.8566,
        "destination_longitude": 2.3522,
        "destination_address": "Paris, France",
        "pickup_time": datetime.now(timezone.utc),
        "delivery_time": datetime.now(timezone.utc) + timedelta(hours=8),
        "total_duration_hours": 8.0,
        "transport_type": {"type": "truck", "capacity": 20},
        "cargo": {"weight": 10, "type": "general"},
        "total_cost": 1000.0,
        "empty_driving": {"distance_km": 200, "duration_hours": 4}
    }
    
    # Create
    route = Route(**route_data)
    db_session.add(route)
    db_session.commit()
    
    # Read
    db_route = db_session.query(Route).filter(Route.id == route.id).first()
    assert db_route is not None
    assert db_route.origin_address == "Berlin, Germany"
    assert db_route.transport_type["type"] == "truck"
    assert db_route.empty_driving["distance_km"] == 200
    
    # Update
    db_route.total_cost = 1200.0
    db_session.commit()
    updated_route = db_session.query(Route).filter(Route.id == route.id).first()
    assert updated_route.total_cost == 1200.0
    
    # Delete
    db_session.delete(db_route)
    db_session.commit()
    deleted_route = db_session.query(Route).filter(Route.id == route.id).first()
    assert deleted_route is None

def test_offer_with_route_relationship(db_session):
    """Test offer creation with route relationship and complex cost breakdown"""
    # Create a route first
    route_data = {
        "origin_latitude": 52.5200,
        "origin_longitude": 13.4050,
        "origin_address": "Berlin, Germany",
        "destination_latitude": 48.8566,
        "destination_longitude": 2.3522,
        "destination_address": "Paris, France",
        "pickup_time": datetime.now(timezone.utc),
        "delivery_time": datetime.now(timezone.utc) + timedelta(hours=8),
        "total_duration_hours": 8.0,
        "total_cost": 1000.0
    }
    route = Route(**route_data)
    db_session.add(route)
    db_session.commit()
    
    # Create detailed cost breakdown
    cost_breakdown = {
        "fuel": 300.0,
        "driver_wages": 400.0,
        "tolls": 100.0,
        "empty_driving": 150.0,
        "maintenance": 50.0
    }
    
    # Create offer
    offer = Offer(
        route_id=route.id,
        total_cost=sum(cost_breakdown.values()),
        margin=0.2,
        final_price=1200.0,
        fun_fact="The route from Berlin to Paris covers multiple historic trade routes!",
        status="pending",
        cost_breakdown=cost_breakdown
    )
    db_session.add(offer)
    db_session.commit()
    
    # Verify offer with relationships
    db_offer = db_session.query(Offer).filter(Offer.route_id == route.id).first()
    assert db_offer is not None
    assert db_offer.route.origin_address == "Berlin, Germany"
    assert db_offer.cost_breakdown["fuel"] == 300.0
    assert len(db_offer.cost_breakdown) == 5
    assert db_offer.total_cost == 1000.0

def test_cost_settings_operations(db_session):
    """Test cost settings operations with different categories"""
    # Create various cost settings
    settings = [
        CostItem(
            type="fuel",
            category="variable",
            base_value=1.5,  # EUR per liter
            multiplier=1.0,
            currency="EUR",
            description="Standard fuel rate per liter"
        ),
        CostItem(
            type="driver_base",
            category="fixed",
            base_value=25.0,  # EUR per hour
            multiplier=1.0,
            currency="EUR",
            description="Base driver rate per hour"
        ),
        CostItem(
            type="driver_overtime",
            category="fixed",
            base_value=25.0,  # EUR per hour
            multiplier=1.5,  # 150% for overtime
            currency="EUR",
            description="Overtime driver rate per hour"
        ),
        CostItem(
            type="toll",
            category="variable",
            base_value=0.2,  # EUR per km
            multiplier=1.0,
            currency="EUR",
            description="Average toll cost per kilometer"
        )
    ]
    
    # Add all settings
    for setting in settings:
        db_session.add(setting)
    db_session.commit()
    
    # Verify all settings were created
    db_settings = db_session.query(CostItem).all()
    assert len(db_settings) == 4
    
    # Test filtering by category
    variable_costs = db_session.query(CostItem).filter(
        CostItem.category == "variable"
    ).all()
    assert len(variable_costs) == 2  # fuel and toll
    
    fixed_costs = db_session.query(CostItem).filter(
        CostItem.category == "fixed"
    ).all()
    assert len(fixed_costs) == 2  # driver base and overtime
    
    # Test updating a setting
    fuel_setting = db_session.query(CostItem).filter(
        CostItem.type == "fuel"
    ).first()
    fuel_setting.base_value = 1.8  # Increase fuel rate
    db_session.commit()
    
    updated_fuel = db_session.query(CostItem).filter(
        CostItem.type == "fuel"
    ).first()
    assert updated_fuel.base_value == 1.8

def test_create_route(db_session):
    repo = Repository(db_session)
    
    # Create test route data
    route_data = {
        "origin_latitude": 52.5200,
        "origin_longitude": 13.4050,
        "origin_address": "Berlin, Germany",
        "destination_latitude": 48.8566,
        "destination_longitude": 2.3522,
        "destination_address": "Paris, France",
        "pickup_time": datetime.now(timezone.utc),
        "delivery_time": datetime.now(timezone.utc) + timedelta(hours=8),
        "total_duration_hours": 8.0,
        "transport_type": {"type": "truck", "capacity": 20},
        "cargo": {"weight": 10, "type": "general"},
        "total_cost": 1000.0
    }
    
    route = repo.create_route(route_data)
    assert route.id is not None
    assert route.origin_address == "Berlin, Germany"
    assert route.destination_address == "Paris, France"

def test_create_offer(db_session):
    # First create a route
    repo = Repository(db_session)
    route_data = {
        "origin_latitude": 52.5200,
        "origin_longitude": 13.4050,
        "origin_address": "Berlin, Germany",
        "destination_latitude": 48.8566,
        "destination_longitude": 2.3522,
        "destination_address": "Paris, France",
        "pickup_time": datetime.now(timezone.utc),
        "delivery_time": datetime.now(timezone.utc) + timedelta(hours=8),
        "total_duration_hours": 8.0,
        "total_cost": 1000.0
    }
    route = repo.create_route(route_data)
    
    # Create an offer
    offer = Offer(
        route_id=route.id,
        total_cost=1000.0,
        margin=0.2,
        final_price=1200.0,
        fun_fact="Did you know? The distance between Berlin and Paris is about 1,054 kilometers!",
        status="pending",
        cost_breakdown={"fuel": 500, "driver": 400, "other": 100}
    )
    
    db_session.add(offer)
    db_session.commit()
    
    # Verify offer was created
    db_offer = db_session.query(Offer).filter(Offer.route_id == route.id).first()
    assert db_offer is not None
    assert db_offer.total_cost == 1000.0
    assert db_offer.final_price == 1200.0

def test_create_cost_setting(db_session):
    # Create cost settings for different cost types
    cost_settings = [
        CostItem(
            type="fuel",
            category="variable",
            base_value=1.5,  # EUR per liter
            multiplier=1.0,
            currency="EUR",
            description="Standard fuel rate per liter"
        ),
        CostItem(
            type="driver",
            category="fixed",
            base_value=25.0,  # EUR per hour
            multiplier=1.2,  # overtime multiplier
            currency="EUR",
            description="Driver hourly rate"
        ),
        CostItem(
            type="maintenance",
            category="variable",
            base_value=0.15,  # EUR per km
            multiplier=1.0,
            currency="EUR",
            description="Vehicle maintenance cost per kilometer"
        )
    ]
    
    for setting in cost_settings:
        db_session.add(setting)
    db_session.commit()
    
    # Verify cost settings were created
    db_settings = db_session.query(CostItem).all()
    assert len(db_settings) == 3
    
    # Check specific setting
    fuel_setting = db_session.query(CostItem).filter(CostItem.type == "fuel").first()
    assert fuel_setting is not None
    assert fuel_setting.base_value == 1.5
    assert fuel_setting.currency == "EUR"
    assert fuel_setting.is_enabled == True
