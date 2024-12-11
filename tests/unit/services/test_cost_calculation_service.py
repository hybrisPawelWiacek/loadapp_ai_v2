import pytest
from datetime import datetime, timedelta, UTC
from uuid import uuid4
from unittest.mock import patch

from backend.domain.services.cost_calculation_service import CostCalculationService
from backend.domain.entities.route import Route, MainRoute, EmptyDriving, CountrySegment
from backend.domain.entities.location import Location
from backend.domain.entities.timeline import TimelineEvent
from backend.domain.entities.cargo import TransportType, Cargo

class TestCostCalculationService:
    @pytest.fixture
    def cost_service(self):
        """Initialize cost calculation service"""
        return CostCalculationService()

    @pytest.fixture
    def sample_route(self, mock_location):
        """Create a sample route for testing"""
        return Route(
            id=uuid4(),
            origin=mock_location,
            destination=Location(
                latitude=48.8566,
                longitude=2.3522,
                address="Paris, France"
            ),
            pickup_time=datetime.now(),
            delivery_time=datetime.now() + timedelta(days=1),
            empty_driving=EmptyDriving(),
            main_route=MainRoute(
                distance_km=1000.0,
                duration_hours=12.0,
                country_segments=[
                    CountrySegment(
                        country="Germany",
                        distance_km=400.0,
                        duration_hours=5.0
                    ),
                    CountrySegment(
                        country="France",
                        distance_km=600.0,
                        duration_hours=7.0
                    )
                ]
            ),
            timeline=[
                TimelineEvent(
                    event_type="start",
                    location=mock_location,
                    planned_time=datetime.now(),
                    duration_minutes=0,
                    description="Start of route",
                    is_required=True
                )
            ],
            transport_type=None,
            cargo=None,
            is_feasible=True,
            total_cost=0.0,
            currency="EUR",
            cost_breakdown={},
            optimization_insights={}
        )

    @pytest.fixture
    def cost_settings(self):
        """Create sample cost settings"""
        return [
            {
                "id": str(uuid4()),
                "type": "fuel",
                "category": "variable",
                "base_value": 1.5,
                "multiplier": 1.0,
                "currency": "EUR",
                "is_enabled": True
            },
            {
                "id": str(uuid4()),
                "type": "driver",
                "category": "variable",
                "base_value": 30.0,
                "multiplier": 1.0,
                "currency": "EUR",
                "is_enabled": True
            }
        ]

    def test_calculate_route_cost(self, cost_service, sample_route, cost_settings):
        """Test basic route cost calculation"""
        result = cost_service.calculate_route_cost(sample_route, cost_settings)
        
        assert result is not None
        assert "total_cost" in result
        assert "cost_breakdown" in result
        assert result["total_cost"] > 0

    def test_calculate_variable_costs(self, cost_service, sample_route, cost_settings):
        """Test variable cost calculations"""
        variable_costs = cost_service._calculate_variable_costs(
            sample_route,
            [s for s in cost_settings if s["category"] == "variable"]
        )
        
        assert "fuel" in variable_costs
        assert "driver" in variable_costs
        assert variable_costs["fuel"] == sample_route.main_route.distance_km * 1.5
        assert variable_costs["driver"] == sample_route.main_route.duration_hours * 30.0

    def test_disabled_cost_items(self, cost_service, sample_route, cost_settings):
        """Test handling of disabled cost items"""
        # Disable fuel cost
        disabled_settings = cost_settings.copy()
        disabled_settings[0]["is_enabled"] = False
        
        result = cost_service.calculate_route_cost(sample_route, disabled_settings)
        
        assert "fuel" not in result["cost_breakdown"]["variable_costs"]
        assert result["total_cost"] < sample_route.main_route.distance_km * 1.5

    def test_cost_calculation_with_empty_settings(self, cost_service, sample_route):
        """Test cost calculation with no settings"""
        result = cost_service.calculate_route_cost(sample_route, [])
        
        assert result["total_cost"] == 0
        assert len(result["cost_breakdown"]["variable_costs"]) == 0

    def test_cost_optimization(self, cost_service, sample_route, cost_settings):
        """Test cost optimization suggestions"""
        result = cost_service.get_optimization_suggestions(
            sample_route,
            cost_settings
        )
        
        assert "suggestions" in result
        assert isinstance(result["suggestions"], list)
        assert len(result["suggestions"]) > 0

    def test_invalid_route_data(self, cost_service, cost_settings):
        """Test handling of invalid route data"""
        invalid_route = Route(
            id=uuid4(),
            origin=None,  # Invalid: missing origin
            destination=None,  # Invalid: missing destination
            empty_driving=EmptyDriving(),
            main_route=MainRoute(
                distance_km=-1.0,  # Invalid: negative distance
                duration_hours=-1.0,  # Invalid: negative duration
                country_segments=[]
            ),
            timeline=[],
            transport_type=None,
            cargo=None,
            is_feasible=False,
            total_cost=0.0,
            currency="EUR",
            cost_breakdown={},
            optimization_insights={}
        )
        
        with pytest.raises(ValueError):
            cost_service.calculate_route_cost(invalid_route, cost_settings)

    def test_cost_calculation_with_timestamp(self, cost_service, sample_route, cost_settings):
        """Test cost calculation with timestamp"""
        with patch('backend.services.cost_calculation_service.datetime') as mock_datetime:
            test_time = datetime(2024, 1, 1, tzinfo=UTC)
            mock_datetime.now.return_value = test_time
            
            result = cost_service.calculate_route_cost(sample_route, cost_settings)
            
            assert result.calculation_time == test_time
