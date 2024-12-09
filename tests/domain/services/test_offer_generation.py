import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4
from pytz import UTC

from backend.domain.services.offer import OfferService
from backend.domain.entities import (
    Route, Location, EmptyDriving, MainRoute, CountrySegment,
    Offer
)
from backend.infrastructure.database.repository import Repository
from backend.infrastructure.external.ai_integration import AIIntegrationService

@pytest.fixture
def mock_repository():
    """Create a mock database repository."""
    repo = Mock(spec=Repository)
    
    # Setup mock behaviors
    repo.save_offer.return_value = None
    repo.get_offer.return_value = Offer(
        id=uuid4(),
        route_id=uuid4(),
        total_cost=1000.0,
        margin=10.0,
        final_price=1100.0,
        cost_breakdown={"total": 1000.0},
        fun_fact="Test fun fact",
        status="active",
        created_at=datetime.now(UTC)
    )
    repo.list_offers.return_value = [
        Offer(
            id=uuid4(),
            route_id=uuid4(),
            total_cost=1000.0,
            margin=10.0,
            final_price=1100.0,
            cost_breakdown={"total": 1000.0},
            fun_fact="Test fun fact",
            status="active",
            created_at=datetime.now(UTC)
        )
    ]
    
    return repo

@pytest.fixture
def mock_ai_service():
    """Create a mock AI integration service."""
    ai_service = Mock(spec=AIIntegrationService)
    ai_service.generate_transport_fun_fact.return_value = "Test fun fact about transport!"
    return ai_service

@pytest.fixture
def mock_route():
    """Create a mock route for testing."""
    return Route(
        id=uuid4(),
        origin=Location(52.52, 13.405, "Berlin, Germany"),
        destination=Location(52.237, 21.017, "Warsaw, Poland"),
        pickup_time=datetime.now(UTC),
        delivery_time=datetime.now(UTC) + timedelta(days=1),
        empty_driving=EmptyDriving(
            distance_km=50.0,
            duration_hours=1.0,
            base_cost=75.0,
            country_segments=[
                CountrySegment(
                    country="Germany",
                    distance_km=50.0
                )
            ]
        ),
        main_route=MainRoute(
            distance_km=700.0,
            duration_hours=9.0,
            base_cost=1050.0,
            country_segments=[
                CountrySegment(
                    country="Germany",
                    distance_km=300.0
                ),
                CountrySegment(
                    country="Poland",
                    distance_km=400.0
                )
            ]
        ),
        timeline=[],
        total_duration_hours=10.0,
        is_feasible=True,
        duration_validation=True
    )

@pytest.fixture
def service(mock_repository, mock_ai_service):
    """Create an offer service instance with mocked dependencies."""
    return OfferService(
        db_repository=mock_repository,
        ai_service=mock_ai_service
    )

def test_generate_offer_basic(service, mock_route):
    """Test basic offer generation with default margin."""
    cost_breakdown = {
        "total": 1000.0,
        "fuel": 500.0,
        "driver": 300.0,
        "toll": 200.0
    }
    
    offer = service.generate_offer(
        route=mock_route,
        cost_breakdown=cost_breakdown
    )
    
    # Verify offer structure
    assert offer is not None
    assert isinstance(offer.id, uuid4().__class__)
    assert offer.route_id == mock_route.id
    assert offer.total_cost == cost_breakdown["total"]
    assert offer.margin == 10.0  # Default margin
    assert offer.final_price == 1100.0  # 1000 + 10%
    assert offer.cost_breakdown == cost_breakdown
    assert offer.fun_fact == "Test fun fact about transport!"
    assert offer.status == "active"
    assert isinstance(offer.created_at, datetime)
    assert offer.created_at.tzinfo == UTC

def test_generate_offer_custom_margin(service, mock_route):
    """Test offer generation with custom margin percentage."""
    cost_breakdown = {"total": 1000.0}
    margin = 15.0
    
    offer = service.generate_offer(
        route=mock_route,
        cost_breakdown=cost_breakdown,
        margin_percentage=margin
    )
    
    assert offer.margin == margin
    assert offer.final_price == 1150.0  # 1000 + 15%

def test_generate_offer_with_ai_error(service, mock_route, mock_ai_service):
    """Test offer generation when AI service fails."""
    # Make AI service fail
    mock_ai_service.generate_transport_fun_fact.side_effect = Exception("AI service error")
    
    offer = service.generate_offer(
        route=mock_route,
        cost_breakdown={"total": 1000.0}
    )
    
    # Offer should still be generated, but without fun fact
    assert offer is not None
    assert offer.fun_fact is None

def test_get_offer(service):
    """Test retrieving an offer by ID."""
    offer_id = str(uuid4())
    offer = service.get_offer(offer_id)
    
    assert offer is not None
    assert isinstance(offer, Offer)
    assert offer.status == "active"

def test_get_nonexistent_offer(service, mock_repository):
    """Test retrieving a non-existent offer."""
    mock_repository.get_offer.return_value = None
    offer_id = str(uuid4())
    
    offer = service.get_offer(offer_id)
    assert offer is None

def test_list_offers(service):
    """Test listing offers with pagination."""
    offers = service.list_offers(limit=10, offset=0)
    
    assert isinstance(offers, list)
    assert len(offers) > 0
    assert all(isinstance(offer, Offer) for offer in offers)

def test_list_offers_empty(service, mock_repository):
    """Test listing offers when none exist."""
    mock_repository.list_offers.return_value = []
    
    offers = service.list_offers(limit=10, offset=0)
    assert isinstance(offers, list)
    assert len(offers) == 0

def test_generate_offer_database_error(service, mock_route, mock_repository):
    """Test offer generation when database save fails."""
    mock_repository.save_offer.side_effect = Exception("Database error")
    
    with pytest.raises(Exception) as exc_info:
        service.generate_offer(
            route=mock_route,
            cost_breakdown={"total": 1000.0}
        )
    
    assert "Database error" in str(exc_info.value)

def test_offer_currency(service, mock_route):
    """Test offer generation with different currency."""
    cost_breakdown = {"total": 1000.0}
    currency = "USD"
    
    offer = service.generate_offer(
        route=mock_route,
        cost_breakdown=cost_breakdown,
        currency=currency
    )
    
    assert offer.currency == currency

def test_offer_validation(service, mock_route):
    """Test offer generation with invalid inputs."""
    # Test with negative total cost
    with pytest.raises(ValueError):
        service.generate_offer(
            route=mock_route,
            cost_breakdown={"total": -1000.0}
        )
    
    # Test with negative margin
    with pytest.raises(ValueError):
        service.generate_offer(
            route=mock_route,
            cost_breakdown={"total": 1000.0},
            margin_percentage=-10.0
        )
