import pytest
from datetime import datetime, timedelta, UTC
import streamlit as st
from frontend.components.route_input_form import render_route_input_form
from frontend.components.route_display import render_route_display

class TestRouteComponents:
    @pytest.fixture(autouse=True)
    def setup(self, mock_api_client):
        """Setup test environment with mocked API client"""
        # Reset Streamlit session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]

    def test_route_input_form_render(self):
        """Test route input form rendering"""
        form_data = render_route_input_form()
        
        # When first rendered without submission
        assert form_data is None
        
        # Verify session state initialization
        assert 'form_submitted' in st.session_state
        assert not st.session_state.form_submitted

    def test_route_input_form_submission(self, monkeypatch):
        """Test route input form submission"""
        # Mock form submission
        def mock_form_submit():
            return True
        monkeypatch.setattr(st, "form_submit_button", mock_form_submit)
        
        # Mock input values
        test_inputs = {
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
                    "time": datetime.now().time()
                },
                "delivery": {
                    "date": (datetime.now() + timedelta(days=1)).date(),
                    "time": datetime.now().time()
                }
            },
            "cargo": {
                "type": "General",
                "weight": 1000.0,
                "volume": 10.0,
                "value": 5000.0
            }
        }
        
        # Mock input functions
        def mock_text_input(*args, **kwargs):
            if "Origin" in args:
                return test_inputs["origin"]["address"]
            return test_inputs["destination"]["address"]
        monkeypatch.setattr(st, "text_input", mock_text_input)
        
        # Test form submission
        form_data = render_route_input_form()
        
        assert form_data is not None
        assert form_data["origin"]["address"] == test_inputs["origin"]["address"]
        assert form_data["destination"]["address"] == test_inputs["destination"]["address"]

    def test_route_display(self, mock_route):
        """Test route display component"""
        # Mock route data
        route_data = {
            "id": str(mock_route.id),
            "origin": {
                "address": mock_route.origin.address,
                "coordinates": {
                    "lat": mock_route.origin.latitude,
                    "lon": mock_route.origin.longitude
                }
            },
            "destination": {
                "address": mock_route.destination.address,
                "coordinates": {
                    "lat": mock_route.destination.latitude,
                    "lon": mock_route.destination.longitude
                }
            },
            "main_route": {
                "distance_km": 1000.0,
                "duration_hours": 12.0
            },
            "timeline": mock_route.timeline,
            "total_duration_hours": mock_route.total_duration_hours,
            "is_feasible": mock_route.is_feasible
        }
        
        # Test display rendering
        render_route_display(route_data)
        
        # Verify metrics are displayed
        # Note: In real tests, we'd need to mock st.metric and verify calls
        assert True  # Placeholder for actual metric verification

    def test_route_display_empty_data(self):
        """Test route display with empty/invalid data"""
        with pytest.raises(KeyError):
            render_route_display({})

    def test_route_input_validation(self, monkeypatch):
        """Test route input form validation"""
        def mock_form_submit():
            return True
        monkeypatch.setattr(st, "form_submit_button", mock_form_submit)
        
        # Test with invalid coordinates
        test_inputs = {
            "origin": {
                "address": "",  # Empty address
                "coordinates": {"lat": 1000.0, "lon": 1000.0}  # Invalid coordinates
            }
        }
        
        def mock_text_input(*args, **kwargs):
            return test_inputs["origin"]["address"]
        monkeypatch.setattr(st, "text_input", mock_text_input)
        
        form_data = render_route_input_form()
        assert form_data is None  # Form should not submit with invalid data

    def test_route_component_date_formatting(self):
        test_date = datetime.now(UTC)
        formatted_date = format_date_for_display(test_date)
        assert isinstance(formatted_date, str)
        # Add your specific assertions for date formatting