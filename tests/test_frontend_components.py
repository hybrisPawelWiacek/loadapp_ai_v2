import pytest
import streamlit as st
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from frontend.components.route_input_form import render_route_input_form
from frontend.components.route_display import render_route_display, render_route_map
from frontend.components.advanced_cost_settings import AdvancedCostSettings, render_cost_settings
from frontend.pages.offer_review import OfferReviewPage, render_offer_review_page

# Mock data for testing
MOCK_FORM_DATA = {
    "origin": {
        "address": "Berlin, Germany",
        "coordinates": {"lat": 52.5200, "lon": 13.4050}
    },
    "destination": {
        "address": "Paris, France",
        "coordinates": {"lat": 48.8566, "lon": 2.3522}
    },
    "schedule": {
        "pickup": {
            "date": datetime.now().date(),
            "time": datetime.now().replace(hour=9, minute=0).time()
        },
        "delivery": {
            "date": (datetime.now() + timedelta(days=1)).date(),
            "time": datetime.now().replace(hour=17, minute=0).time()
        }
    },
    "cargo": {
        "type": "General",
        "transport_type": "Standard Truck",
        "weight": 1000.0,
        "volume": 10.0,
        "value": 5000.0,
        "special_requirements": ["Temperature Control"]
    }
}

MOCK_ROUTE_DATA = {
    "id": "route123",
    "origin": {"address": "Berlin, Germany"},
    "destination": {"address": "Paris, France"},
    "pickup_time": "2024-01-01T09:00:00",
    "delivery_time": "2024-01-01T17:00:00",
    "total_distance_km": 1000,
    "total_duration_hours": 12,
    "empty_driving": {"distance_km": 50, "duration_hours": 1},
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
            "planned_time": "2024-01-01T17:00:00",
            "duration_minutes": 30,
            "description": "Unloading cargo",
            "is_required": True
        }
    ],
    "is_feasible": True,
    "duration_validation": True
}

MOCK_COST_SETTINGS = [
    {
        "id": "cost1",
        "type": "fuel",
        "is_enabled": True,
        "base_value": 100.0,
        "multiplier": 1.0
    },
    {
        "id": "cost2",
        "type": "driver",
        "is_enabled": True,
        "base_value": 200.0,
        "multiplier": 1.5
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
def mock_requests():
    """Mock requests for API calls."""
    with patch("requests.get") as mock_get, patch("requests.post") as mock_post:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = MOCK_COST_SETTINGS
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "success"}
        yield mock_get, mock_post

def test_route_input_form_structure():
    """Test RouteInputForm component structure and interface."""
    with patch("streamlit.form") as mock_form:
        with patch("streamlit.text_input") as mock_input:
            mock_form.return_value.__enter__.return_value = None
            mock_input.return_value = "Berlin, Germany"
            
            form_data = render_route_input_form()
            assert form_data is None  # Should return None when not submitted
            
            # Verify form structure matches mix_final_scope2.md requirements
            mock_form.assert_called_once_with("route_form")
            mock_input.assert_called()

def test_route_display_component():
    """Test RouteDisplay component rendering and functionality."""
    with patch("streamlit.markdown") as mock_markdown:
        with patch("streamlit.metric") as mock_metric:
            render_route_display(MOCK_ROUTE_DATA)
            
            # Verify metrics are displayed correctly
            mock_metric.assert_any_call("Total Distance", "1000.0 km")
            mock_metric.assert_any_call("Duration", "12.0 hours")
            mock_metric.assert_any_call("Empty Driving", "50.0 km")

def test_advanced_cost_settings():
    """Test AdvancedCostSettings component."""
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = MOCK_COST_SETTINGS
        
        settings = AdvancedCostSettings()
        assert settings.fetch_settings() is True
        assert len(settings.settings) == 2
        assert settings.settings[0].type == "fuel"
        assert settings.settings[1].type == "driver"

def test_offer_review_page():
    """Test OfferReviewPage component structure and functionality."""
    with patch("streamlit.sidebar.date_input") as mock_date_input:
        with patch("streamlit.sidebar.number_input") as mock_number_input:
            page = OfferReviewPage()
            filters = page._initialize_filters()
            
            assert hasattr(filters, "start_date")
            assert hasattr(filters, "end_date")
            assert hasattr(filters, "min_price")
            assert hasattr(filters, "max_price")
            
            mock_date_input.assert_called_once()
            mock_number_input.assert_called()

def test_type_safety():
    """Test type safety of component interfaces."""
    # Test RouteInputForm data structure
    with patch("streamlit.form") as mock_form:
        mock_form.return_value.__enter__.return_value = None
        form_data = render_route_input_form()
        assert form_data is None or isinstance(form_data, dict)
    
    # Test AdvancedCostSettings type safety
    settings = AdvancedCostSettings()
    assert hasattr(settings, "settings")
    assert isinstance(settings.settings, list)
    
    # Test OfferReviewPage type safety
    page = OfferReviewPage()
    assert hasattr(page, "filters")
    assert hasattr(page, "offers")
    assert hasattr(page, "df")

def test_component_integration():
    """Test integration between components."""
    with patch("streamlit.session_state", create=True) as mock_state:
        mock_state.current_route = MOCK_ROUTE_DATA
        
        # Test route display integration
        with patch("streamlit.markdown"):
            with patch("streamlit.metric"):
                render_route_display(mock_state.current_route)
                render_route_map(mock_state.current_route)
        
        # Test cost settings integration
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = MOCK_COST_SETTINGS
            render_cost_settings()

def test_error_handling():
    """Test error handling in components."""
    # Test RouteDisplay with invalid data
    with patch("streamlit.error") as mock_error:
        render_route_display({})
        mock_error.assert_called()
    
    # Test AdvancedCostSettings with API error
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 500
        settings = AdvancedCostSettings()
        assert settings.fetch_settings() is False
    
    # Test OfferReviewPage with API error
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 500
        page = OfferReviewPage()
        assert page.fetch_offers() is False
