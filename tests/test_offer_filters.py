import pytest
from datetime import datetime, timedelta, UTC
from uuid import uuid4
from typing import List, Dict, Any

from backend.domain.entities.offer import Offer, OfferStatus
from backend.domain.services.offer_service import OfferService
from backend.infrastructure.database.models import OfferModel
from backend.infrastructure.database.repository import Repository

@pytest.fixture
def test_offers(db_session) -> List[Dict[str, Any]]:
    """Create a set of test offers with various attributes."""
    offers = []
    base_date = datetime.now(UTC)
    
    # Create 100 test offers with different attributes
    for i in range(100):
        offer = OfferModel(
            id=str(uuid4()),
            route_id=str(uuid4()),
            final_price=1000 + (i * 100),  # Prices from 1000 to 10900
            margin_percentage=10.0,
            currency="EUR" if i % 3 == 0 else "USD" if i % 3 == 1 else "GBP",
            status=OfferStatus.DRAFT.value if i % 4 == 0 else
                   OfferStatus.PENDING.value if i % 4 == 1 else
                   OfferStatus.ACCEPTED.value if i % 4 == 2 else
                   OfferStatus.REJECTED.value,
            created_at=base_date - timedelta(days=i % 30),
            updated_at=base_date,
            version=1,
            created_by="test_user",
            updated_by="test_user",
            geographic_restrictions={
                "allowed_countries": ["Germany", "France"] if i % 2 == 0 else ["Spain", "Italy"],
                "allowed_regions": ["Western Europe"] if i % 2 == 0 else ["Mediterranean"]
            }
        )
        db_session.add(offer)
        offers.append(offer)
    
    db_session.commit()
    return offers

def test_list_offers_with_filters(client, test_offers):
    """Test various filter combinations for the /offers endpoint."""
    
    # Test date range filter
    response = client.get("/offers", query_string={
        "start_date": (datetime.now(UTC) - timedelta(days=15)).isoformat(),
        "end_date": datetime.now(UTC).isoformat()
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["offers"]) <= 15  # Should only return offers from last 15 days
    
    # Test price range filter
    response = client.get("/offers", query_string={
        "min_price": 2000,
        "max_price": 5000
    })
    assert response.status_code == 200
    data = response.json()
    for offer in data["offers"]:
        assert 2000 <= offer["final_price"] <= 5000
    
    # Test status filter
    response = client.get("/offers", query_string={
        "status": "DRAFT"
    })
    assert response.status_code == 200
    data = response.json()
    for offer in data["offers"]:
        assert offer["status"] == "DRAFT"
    
    # Test combined filters
    response = client.get("/offers", query_string={
        "start_date": (datetime.now(UTC) - timedelta(days=7)).isoformat(),
        "end_date": datetime.now(UTC).isoformat(),
        "min_price": 3000,
        "max_price": 6000,
        "status": "PENDING",
        "currency": "EUR"
    })
    assert response.status_code == 200
    data = response.json()
    for offer in data["offers"]:
        assert offer["status"] == "PENDING"
        assert offer["currency"] == "EUR"
        assert 3000 <= offer["final_price"] <= 6000
        created_at = datetime.fromisoformat(offer["created_at"])
        assert created_at >= datetime.now(UTC) - timedelta(days=7)

def test_offers_pagination(client, test_offers):
    """Test pagination functionality and performance."""
    import time
    
    # Test first page
    start_time = time.time()
    response = client.get("/offers", query_string={
        "limit": 10,
        "offset": 0
    })
    first_page_time = time.time() - start_time
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["offers"]) == 10
    first_page_ids = [offer["id"] for offer in data["offers"]]
    
    # Test second page
    start_time = time.time()
    response = client.get("/offers", query_string={
        "limit": 10,
        "offset": 10
    })
    second_page_time = time.time() - start_time
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["offers"]) == 10
    second_page_ids = [offer["id"] for offer in data["offers"]]
    
    # Ensure no overlap between pages
    assert not set(first_page_ids).intersection(set(second_page_ids))
    
    # Performance assertions
    assert first_page_time < 1.0  # Should respond within 1 second
    assert second_page_time < 1.0
    assert abs(first_page_time - second_page_time) < 0.1  # Consistent performance

def test_settings_display(client, test_offers):
    """Test the inclusion of settings in offer responses."""
    
    # Test without settings
    response = client.get("/offers", query_string={
        "limit": 5
    })
    assert response.status_code == 200
    data = response.json()
    for offer in data["offers"]:
        assert "applied_settings" not in offer
    
    # Test with settings
    response = client.get("/offers", query_string={
        "limit": 5,
        "include_settings": "true"
    })
    assert response.status_code == 200
    data = response.json()
    for offer in data["offers"]:
        assert "applied_settings" in offer
        assert isinstance(offer["applied_settings"], dict)
        # Verify settings structure
        settings = offer["applied_settings"]
        assert "cost_settings" in settings
        assert "route_settings" in settings
        assert "pricing_settings" in settings
