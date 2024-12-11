import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from pytz import UTC

from backend.domain.entities.route import Route, MainRoute
from backend.domain.entities.location import Location
from backend.domain.entities.offer import (
    Offer, Currency, OfferStatus, CostBreakdown,
    GeographicRestriction
)
from backend.domain.services.offer_service import OfferService
from backend.domain.services.cost_calculation_service import CostCalculationService

@pytest.fixture
def mock_repository():
    return Mock()

@pytest.fixture
def mock_cost_service():
    return Mock()

@pytest.fixture
def mock_ai_service():
    return Mock()

@pytest.fixture
def mock_insights_service():
    return Mock()

@pytest.fixture
def offer_service(mock_repository, mock_cost_service, mock_ai_service, mock_insights_service):
    return OfferService(
        db_repository=mock_repository,
        cost_service=mock_cost_service,
        ai_service=mock_ai_service,
        insights_service=mock_insights_service
    )

@pytest.fixture
def sample_route():
    return Route(
        id=str(uuid4()),
        origin=Location(latitude=52.52, longitude=13.405, address="Berlin"),
        destination=Location(latitude=48.8566, longitude=2.3522, address="Paris"),
        main_route=MainRoute(
            distance=1000000,  # 1000 km in meters
            duration=36000,    # 10 hours in seconds
            polyline="test_polyline",
            country_segments=[
                {"country": "DE", "distance_km": 500, "duration_hours": 5},
                {"country": "FR", "distance_km": 500, "duration_hours": 5}
            ]
        ),
        pickup_time=datetime.now(UTC),
        delivery_time=datetime.now(UTC) + timedelta(days=1),
        total_cost=1000.0,
        currency="EUR"
    )

@pytest.fixture
def sample_cost_breakdown():
    return {
        "cost_breakdown": {
            "base_costs": 300.0,
            "variable_costs": 500.0,
            "cargo_specific_costs": 200.0,
            "total": 1000.0
        },
        "optimization_insights": {
            "suggestions": ["Consider night delivery for lower costs"],
            "potential_savings": 150.0
        }
    }

@pytest.fixture
def sample_offer(sample_route):
    return Offer(
        id=uuid4(),
        route_id=sample_route.id,
        cost_breakdown=CostBreakdown(
            base_costs=300.0,
            variable_costs=500.0,
            cargo_costs=200.0,
            total_cost=1000.0,
            currency=Currency.EUR
        ),
        margin_percentage=15.0,
        final_price=1150.0,
        currency=Currency.EUR,
        status=OfferStatus.DRAFT,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        version=1
    )

def test_generate_offer_success(offer_service, mock_repository, mock_cost_service, sample_route, sample_cost_breakdown):
    """Test successful offer generation with all features."""
    # Setup
    cost_settings = {"base_rate": 1.5, "distance_rate": 0.8}
    margin = 15.0
    mock_cost_service.calculate_route_cost.return_value = sample_cost_breakdown

    # Execute
    result = offer_service.generate_offer(
        route=sample_route,
        cost_settings=cost_settings,
        margin_percentage=margin,
        client_name="Test Client",
        client_contact="test@client.com"
    )

    # Verify
    assert isinstance(result, Offer)
    assert result.route_id == sample_route.id
    assert result.margin_percentage == margin
    assert result.final_price == 1150.0  # 1000 * (1 + 15%)
    assert result.status == OfferStatus.DRAFT
    assert result.client_name == "Test Client"
    assert result.client_contact == "test@client.com"
    assert result.cost_breakdown.total_cost == 1000.0

def test_generate_offer_with_geographic_restrictions(offer_service, sample_route, mock_cost_service, sample_cost_breakdown):
    """Test offer generation with geographic restrictions."""
    # Setup
    mock_cost_service.calculate_route_cost.return_value = sample_cost_breakdown
    geo_restrictions = {
        "allowed_countries": ["DE", "FR"],
        "allowed_regions": ["EU"],
        "restricted_zones": ["ALPS"]
    }

    # Execute
    result = offer_service.generate_offer(
        route=sample_route,
        cost_settings={},
        geographic_restrictions=geo_restrictions
    )

    # Verify
    assert result.geographic_restrictions is not None
    assert "DE" in result.geographic_restrictions.allowed_countries
    assert "EU" in result.geographic_restrictions.allowed_regions
    assert "ALPS" in result.geographic_restrictions.restricted_zones

def test_get_offer_with_includes(offer_service, mock_repository, sample_offer):
    """Test retrieving an offer with optional includes."""
    # Setup
    mock_repository.get_offer_by_id.return_value = sample_offer

    # Execute - with all includes
    result = offer_service.get_offer(
        offer_id=sample_offer.id,
        include_settings=True,
        include_history=True,
        include_metrics=True
    )

    # Verify
    assert result is not None
    assert result.id == sample_offer.id
    assert hasattr(result, 'applied_settings')
    assert hasattr(result, '_version_history')
    assert hasattr(result, '_metrics')

    # Execute - without includes
    result = offer_service.get_offer(
        offer_id=sample_offer.id,
        include_settings=False,
        include_history=False,
        include_metrics=False
    )

    # Verify
    assert result.applied_settings == {}
    assert result._version_history == []
    assert result._metrics is None

def test_list_offers_with_filters(offer_service, mock_repository, sample_offer):
    """Test listing offers with various filters."""
    # Setup
    mock_repository.get_offers.return_value = ([sample_offer], 1)
    
    filters = {
        'start_date': datetime.now(UTC) - timedelta(days=7),
        'end_date': datetime.now(UTC),
        'min_price': 1000.0,
        'max_price': 2000.0,
        'status': 'DRAFT',
        'currency': 'EUR',
        'countries': ['DE', 'FR'],
        'client_id': uuid4()
    }

    # Execute
    offers, total = offer_service.list_offers(
        filters=filters,
        include_settings=True,
        include_history=True,
        page=1,
        page_size=10
    )

    # Verify
    assert len(offers) == 1
    assert total == 1
    mock_repository.get_offers.assert_called_once()
    call_kwargs = mock_repository.get_offers.call_args[1]
    assert call_kwargs['start_date'] == filters['start_date']
    assert call_kwargs['min_price'] == filters['min_price']
    assert call_kwargs['currency'] == filters['currency']

def test_update_offer(offer_service, mock_repository, sample_offer):
    """Test updating an offer."""
    # Setup
    mock_repository.get_offer_by_id.return_value = sample_offer
    updates = {
        'margin_percentage': 20.0,
        'client_name': 'Updated Client'
    }
    user_id = "test_user"
    reason = "Price adjustment"

    # Execute
    result = offer_service.update_offer(
        offer_id=sample_offer.id,
        updates=updates,
        user_id=user_id,
        reason=reason
    )

    # Verify
    assert result.margin_percentage == 20.0
    assert result.client_name == 'Updated Client'
    assert result.version > 1
    mock_repository.save_offer.assert_called_once()

def test_delete_offer(offer_service, mock_repository, sample_offer):
    """Test soft deleting an offer."""
    # Setup
    mock_repository.get_offer_by_id.return_value = sample_offer
    mock_repository.soft_delete_offer.return_value = True
    user_id = "test_user"
    reason = "Client request"

    # Execute
    result = offer_service.delete_offer(
        offer_id=sample_offer.id,
        user_id=user_id,
        reason=reason
    )

    # Verify
    assert result is True
    mock_repository.soft_delete_offer.assert_called_once_with(sample_offer.id)

def test_offer_version_history(offer_service, mock_repository, sample_offer):
    """Test offer version history creation."""
    # Setup
    mock_repository.create.return_value = sample_offer
    mock_repository.create_version.return_value = True

    # Execute
    offer_service._save_with_version_history(sample_offer)

    # Verify
    mock_repository.create.assert_called_once()
    mock_repository.create_version.assert_called_once()
    version_data = mock_repository.create_version.call_args[0][0]
    assert version_data['entity_id'] == sample_offer.id
    assert version_data['version'] == sample_offer.version
    assert 'data' in version_data
    assert 'created_at' in version_data
