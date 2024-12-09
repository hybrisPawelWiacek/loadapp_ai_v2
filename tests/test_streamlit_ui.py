import pytest
import requests
from datetime import datetime, timedelta
import json
from unittest.mock import patch, MagicMock
from frontend.components.route_input_form import render_route_input_form
from frontend.components.route_display import render_route_display, render_route_map
from frontend.components.advanced_cost_settings import render_cost_settings
from frontend.pages.offer_review import render_offer_review_page

# Constants
API_URL = "http://127.0.0.1:5000"
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# Mock response data
MOCK_ROUTE_RESPONSE = {
    "id": "route123",
    "origin": {"address": "Berlin, Germany"},
    "destination": {"address": "Paris, France"},
    "pickup_time": "2024-01-01T09:00:00",
    "delivery_time": "2024-01-01T21:00:00",
    "total_distance_km": 1000,
    "total_duration_hours": 12,
    "empty_driving": {
        "distance_km": 50,
        "duration_hours": 1
    },
    "timeline": [
        {
            "event_type": "pickup",
            "location": {"address": "Berlin, Germany"},
            "planned_time": "2024-01-01T09:00:00",
            "duration_minutes": 30,
            "description": "Loading cargo",
            "is_required": True
        },
        {
            "event_type": "delivery",
            "location": {"address": "Paris, France"},
            "planned_time": "2024-01-01T21:00:00",
            "duration_minutes": 30,
            "description": "Unloading cargo",
            "is_required": True
        }
    ],
    "is_feasible": True,
    "duration_validation": True
}

MOCK_COSTS_RESPONSE = {
    "id": "costs123",
    "base_cost": 800.0,
    "additional_costs": 200.0,
    "total_cost": 1000.0,
    "breakdown": {
        "fuel": 500.0,
        "driver": 300.0,
        "maintenance": 200.0
    }
}

MOCK_OFFER_RESPONSE = {
    "id": "offer123",
    "route_id": "route123",
    "costs_id": "costs123",
    "created_at": "2024-01-01T10:00:00",
    "status": "pending",
    "final_price": 1200.0,
    "margin_percentage": 20,
    "client_name": "Test Client",
    "client_contact": "test@client.com",
    "ai_insights": [
        "This route crosses through 3 countries!",
        "Popular route with high demand"
    ]
}

# Mock data for offer review tests
MOCK_REVIEW_OFFERS = [
    {
        "id": "offer123",
        "route_id": "route123",
        "costs_id": "costs123",
        "created_at": "2024-01-01T10:00:00",
        "status": "completed",
        "final_price": 1200.0,
        "margin_percentage": 20,
        "client_name": "Test Client",
        "client_contact": "test@client.com",
        "route": {
            "origin": "Berlin, Germany",
            "destination": "Paris, France",
            "total_distance_km": 1000,
            "total_duration_hours": 12
        },
        "costs": [
            {"type": "fuel", "amount": 500.0},
            {"type": "driver", "amount": 300.0},
            {"type": "maintenance", "amount": 200.0}
        ],
        "ai_insights": [
            "This route crosses through 3 countries!",
            "Popular route with high demand"
        ]
    },
    {
        "id": "offer124",
        "route_id": "route124",
        "costs_id": "costs124",
        "created_at": "2024-01-02T10:00:00",
        "status": "pending",
        "final_price": 920.0,
        "margin_percentage": 15,
        "client_name": "Another Client",
        "client_contact": "another@client.com",
        "route": {
            "origin": "Munich, Germany",
            "destination": "Amsterdam, Netherlands",
            "total_distance_km": 800,
            "total_duration_hours": 10
        },
        "costs": [
            {"type": "fuel", "amount": 400.0},
            {"type": "driver", "amount": 250.0},
            {"type": "maintenance", "amount": 150.0}
        ],
        "ai_insights": [
            "This is the most popular route this month!",
            "Optimal for refrigerated cargo"
        ]
    }
]

@pytest.fixture
def mock_streamlit():
    """Mock Streamlit session state and functions."""
    with patch("streamlit.session_state", create=True) as mock_state:
        mock_state.current_route = None
        mock_state.current_costs = None
        mock_state.current_offer = None
        yield mock_state

@pytest.fixture
def mock_api():
    """Mock API responses."""
    with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
        def mock_response(*args, **kwargs):
            mock = MagicMock()
            mock.status_code = 200
            
            if "route/calculate" in args[0]:
                mock.json = lambda: MOCK_ROUTE_RESPONSE
            elif "costs/calculate" in args[0]:
                mock.json = lambda: MOCK_COSTS_RESPONSE
            elif "offer" in args[0]:
                mock.json = lambda: MOCK_OFFER_RESPONSE
            elif "data/review" in args[0]:
                mock.json = lambda: MOCK_REVIEW_OFFERS
            else:
                mock.json = lambda: {}
            
            return mock
        
        mock_post.side_effect = mock_response
        mock_get.side_effect = mock_response
        yield mock_post, mock_get

def test_route_api_integration(mock_streamlit, mock_api):
    """Test route calculation API integration with new components."""
    mock_post, _ = mock_api
    
    # Test route input form submission
    with patch("streamlit.form") as mock_form:
        mock_form.return_value.__enter__.return_value = None
        form_data = render_route_input_form()
        
        if form_data:  # Form submitted
            response = requests.post(
                f"{API_URL}/route/calculate",
                json={
                    "id": "route123",
                    "origin": form_data["origin"],
                    "destination": form_data["destination"],
                    "pickup_time": datetime.combine(
                        form_data["schedule"]["pickup"]["date"],
                        form_data["schedule"]["pickup"]["time"]
                    ).isoformat(),
                    "delivery_time": datetime.combine(
                        form_data["schedule"]["delivery"]["date"],
                        form_data["schedule"]["delivery"]["time"]
                    ).isoformat(),
                    "cargo": form_data["cargo"]
                },
                headers=HEADERS
            )
            
            assert response.status_code == 200
            route_data = response.json()
            assert route_data["id"] == "route123"
            mock_streamlit.current_route = route_data

def test_costs_api_integration(mock_streamlit, mock_api):
    """Test cost calculation API integration."""
    mock_post, _ = mock_api
    mock_streamlit.current_route = MOCK_ROUTE_RESPONSE
    
    response = requests.post(
        f"{API_URL}/costs/calculate",
        json={"route_id": mock_streamlit.current_route["id"]},
        headers=HEADERS
    )
    
    assert response.status_code == 200
    costs_data = response.json()
    assert costs_data["total_cost"] == 1000.0
    mock_streamlit.current_costs = costs_data

def test_offer_api_integration(mock_streamlit, mock_api):
    """Test offer generation API integration."""
    mock_post, _ = mock_api
    mock_streamlit.current_route = MOCK_ROUTE_RESPONSE
    
    response = requests.post(
        f"{API_URL}/offer",
        json={
            "route_id": mock_streamlit.current_route["id"],
            "margin": 15.0
        },
        headers=HEADERS
    )
    
    assert response.status_code in [200, 201]
    offer_data = response.json()
    assert offer_data["id"] == "offer123"
    assert "total_price" in offer_data
    assert "margin_percentage" in offer_data
    mock_streamlit.current_offer = offer_data

def test_error_handling(mock_streamlit, mock_api):
    """Test API error handling with new components."""
    mock_post, _ = mock_api
    mock_post.return_value.status_code = 500
    
    with pytest.raises(Exception):
        response = requests.post(
            f"{API_URL}/route/calculate",
            json={},
            headers=HEADERS
        )
        assert response.status_code == 500

def test_offer_review_page(mock_streamlit, mock_api):
    """Test the offer review page with new component."""
    _, mock_get = mock_api
    
    with patch("streamlit.sidebar.date_input") as mock_date_input:
        with patch("streamlit.sidebar.number_input") as mock_number_input:
            render_offer_review_page()
            
            mock_date_input.assert_called_once()
            mock_number_input.assert_called()
            
            response = requests.get(
                f"{API_URL}/data/review",
                params={
                    "limit": 10,
                    "offset": 0,
                    "min_price": 0,
                    "max_price": 10000,
                    "start_date": datetime.now().date().isoformat(),
                    "end_date": datetime.now().date().isoformat()
                },
                headers=HEADERS
            )
            
            assert response.status_code == 200
            offers = response.json()
            assert len(offers) == 2
            assert offers[0]["id"] == "offer123"
            assert offers[1]["id"] == "offer124"
