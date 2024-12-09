from datetime import datetime, UTC
import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4

from backend.domain.services.offer_service import OfferService
from backend.domain.services.cost_calculation_service import CostCalculationService
from backend.infrastructure.external.ai_integration import AIIntegrationService
from backend.infrastructure.database.repository import Repository
from backend.domain.entities import (
    Route, Location, EmptyDriving, MainRoute,
    Cargo, Offer
)

@pytest.fixture
def mock_cost_service():
    service = Mock(spec=CostCalculationService)
    service.calculate_total_cost.return_value = {
        "driver": 300.0,
        "fuel": 1800.0,
        "insurance": 100.0,
        "maintenance": 240.0,
        "tolls": 50.0,
        "total": 2490.0
    }
    return service

@pytest.fixture
def mock_ai_service():
    service = Mock(spec=AIIntegrationService)
    service.generate_transport_fun_fact.return_value = "Fun fact generation is disabled in test mode."
    return service

@pytest.fixture
def mock_repository():
    repo = Mock(spec=Repository)
    repo.save_offer = AsyncMock()
    repo.get_offer = AsyncMock()
    return repo

@pytest.fixture
def service(mock_cost_service, mock_ai_service, mock_repository):
    return OfferService(
        cost_service=mock_cost_service,
        ai_service=mock_ai_service,
        repository=mock_repository,
        default_margin=0.2
    )

@pytest.fixture
def mock_route():
    return Route(
        id=uuid4(),
        origin=Location(52.52, 13.405, "Berlin, Germany"),
        destination=Location(52.237, 21.017, "Warsaw, Poland"),
        pickup_time=datetime.now(UTC),
        delivery_time=datetime.now(UTC),
        empty_driving=EmptyDriving(50.0, 1.0, 75.0),
        main_route=MainRoute(
            distance_km=700.0,
            duration_hours=9.0,
            country_segments=[
                CountrySegment("Germany", 300.0, 4.0),
                CountrySegment("Poland", 400.0, 5.0)
            ]
        ),
        timeline=[],
        total_duration_hours=10.0,
        is_feasible=True,
        duration_validation=True
    )

@pytest.fixture
def mock_cargo():
    return Cargo(
        id=uuid4(),
        type="General",
        weight=1000.0,
        value=150000.0,
        special_requirements=["ADR", "Temperature controlled"]
    )

@pytest.mark.asyncio
async def test_generate_offer_basic(service, mock_route):
    """Test basic offer generation without cargo"""
    offer = await service.generate_offer(mock_route)
    
    assert isinstance(offer, Offer)
    assert isinstance(offer.id, uuid4().__class__)
    assert offer.route_id == mock_route.id
    assert offer.total_cost == 2490.0
    assert offer.margin == 0.2
    assert offer.final_price == pytest.approx(2988.0)  # 2490 * 1.2
    assert offer.status == "pending"
    assert isinstance(offer.created_at, datetime)
    assert offer.fun_fact == "Fun fact generation is disabled in test mode."

@pytest.mark.asyncio
async def test_generate_offer_with_cargo(service, mock_route, mock_cargo):
    """Test offer generation with cargo"""
    offer = await service.generate_offer(mock_route, mock_cargo)
    
    # Verify cost service was called with cargo
    service.cost_service.calculate_total_cost.assert_called_once_with(
        mock_route, mock_cargo
    )
    
    assert isinstance(offer, Offer)
    assert offer.cost_breakdown == service.cost_service.calculate_total_cost.return_value

@pytest.mark.asyncio
async def test_generate_offer_custom_margin(service, mock_route):
    """Test offer generation with custom margin"""
    custom_margin = 0.25  # 25%
    offer = await service.generate_offer(mock_route, margin=custom_margin)
    
    assert offer.margin == custom_margin
    assert offer.final_price == pytest.approx(3112.5)  # 2490 * 1.25

@pytest.mark.asyncio
async def test_generate_offer_saves_to_db(service, mock_route):
    """Test that generated offer is saved to database"""
    offer = await service.generate_offer(mock_route)
    
    # Verify repository was called
    service.repository.save_offer.assert_called_once_with(offer)

@pytest.mark.asyncio
async def test_update_offer_status(service, mock_route):
    """Test offer status update"""
    # Setup mock offer in repository
    offer = await service.generate_offer(mock_route)
    service.repository.get_offer.return_value = offer
    
    # Update status
    updated_offer = await service.update_offer_status(offer.id, "accepted")
    
    assert updated_offer is not None
    assert updated_offer.status == "accepted"
    service.repository.save_offer.assert_called_with(updated_offer)

@pytest.mark.asyncio
async def test_comprehensive_offer_generation(service, mock_route, mock_cargo):
    """Test complete offer generation process including costs, fun fact, and DB storage"""
    # Setup expected cost breakdown
    expected_costs = {
        "driver": 300.0,
        "fuel": 1800.0,
        "insurance": 100.0,
        "maintenance": 240.0,
        "tolls": 50.0,
        "total": 2490.0
    }
    service.cost_service.calculate_total_cost.return_value = expected_costs
    
    # Setup expected fun fact
    expected_fun_fact = "Fun fact generation is disabled in test mode."
    service.ai_service.generate_transport_fun_fact.return_value = expected_fun_fact
    
    # Generate offer with custom margin
    custom_margin = 0.25  # 25%
    offer = await service.generate_offer(mock_route, mock_cargo, margin=custom_margin)
    
    # Verify all aspects of the generated offer
    assert isinstance(offer, Offer)
    assert isinstance(offer.id, uuid4().__class__)
    assert offer.route_id == mock_route.id
    assert offer.total_cost == expected_costs["total"]
    assert offer.margin == custom_margin
    assert offer.final_price == pytest.approx(expected_costs["total"] * (1 + custom_margin))
    assert offer.status == "pending"
    assert isinstance(offer.created_at, datetime)
    assert offer.fun_fact == expected_fun_fact
    assert offer.cost_breakdown == expected_costs
    
    # Verify interactions with dependencies
    service.cost_service.calculate_total_cost.assert_called_once_with(mock_route, mock_cargo)
    service.ai_service.generate_transport_fun_fact.assert_called_once_with(
        origin=mock_route.origin.address,
        destination=mock_route.destination.address,
        distance_km=mock_route.main_route.distance_km
    )
    service.repository.save_offer.assert_called_once_with(offer)

def test_calculate_margin_options(service):
    """Test margin options calculation"""
    total_cost = 1000.0
    options = service.calculate_margin_options(total_cost)
    
    assert len(options) == 3  # Default steps
    assert "15%" in options  # -5% from default
    assert "20%" in options  # Default margin
    assert "25%" in options  # +5% from default
    
    assert options["20%"] == pytest.approx(1200.0)  # 1000 * 1.2

@pytest.mark.asyncio
async def test_generate_offer_with_failed_ai(service, mock_route):
    """Test offer generation when AI service fails"""
    # Make AI service return None
    service.ai_service.generate_transport_fun_fact.return_value = None
    
    offer = await service.generate_offer(mock_route)
    
    # Should use fallback fun fact
    assert "Transport is one of humanity's oldest industries!" in offer.fun_fact
    assert isinstance(offer, Offer)  # Rest of the offer should be generated normally
