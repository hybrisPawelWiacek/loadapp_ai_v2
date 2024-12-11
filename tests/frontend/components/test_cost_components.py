import pytest
import streamlit as st
from frontend.components.advanced_cost_settings import render_cost_settings, CostSetting
from uuid import uuid4
from datetime import datetime, UTC
import pandas as pd

@pytest.fixture(autouse=True)
def setup_streamlit():
    # Reset Streamlit session state before each test
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Initialize required session state attributes
    st.session_state.cost_settings = []
    st.session_state.preview_costs = None
    st.session_state.original_settings = None

class TestCostComponents:
    @pytest.fixture(autouse=True)
    def setup(self, setup_streamlit):
        """Setup test environment"""
        # Initialize test settings
        self.test_settings = [
            CostSetting(
                id=str(uuid4()),
                type="fuel",
                category="variable",
                is_enabled=True,
                base_value=1.5,
                multiplier=1.0,
                currency="EUR",
                description="Fuel cost per kilometer"
            ),
            CostSetting(
                id=str(uuid4()),
                type="driver",
                category="variable",
                is_enabled=True,
                base_value=30.0,
                multiplier=1.0,
                currency="EUR",
                description="Driver wages per hour"
            )
        ]
        
        # Convert test settings to DataFrame for original_settings
        settings_data = [{
            'ID': s.id,
            'Type': s.type.title(),
            'Category': s.category.title(),
            'Base Value': s.base_value,
            'Multiplier': s.multiplier,
            'Currency': s.currency,
            'Enabled': s.is_enabled,
            'Description': s.description or ''
        } for s in self.test_settings]
        
        st.session_state.cost_settings = self.test_settings
        st.session_state.original_settings = pd.DataFrame(settings_data)

    def test_cost_settings_render(self, monkeypatch):
        """Test cost settings component rendering"""
        # Mock API response
        def mock_fetch_settings(*args, **kwargs):
            return self.test_settings
        
        monkeypatch.setattr("frontend.components.advanced_cost_settings.fetch_settings", mock_fetch_settings)
        
        # Test initial render
        render_cost_settings()
        
        # Verify session state
        assert len(st.session_state.cost_settings) == len(self.test_settings)
        assert st.session_state.cost_settings[0].type == "fuel"
        assert st.session_state.cost_settings[1].type == "driver"

    def test_cost_settings_update(self, monkeypatch):
        """Test updating cost settings"""
        # Mock form submission
        def mock_form_submit():
            return True
        monkeypatch.setattr(st, "form_submit_button", mock_form_submit)
        
        # Mock API responses
        def mock_get_json(*args, **kwargs):
            return {"settings": [s.__dict__ for s in self.test_settings]}
        
        def mock_post_json(*args, **kwargs):
            return {"success": True, "settings": [s.__dict__ for s in self.test_settings]}
        
        monkeypatch.setattr("requests.get", lambda *args, **kwargs: type('Response', (), {
            'status_code': 200,
            'get_json': mock_get_json
        })())
        
        monkeypatch.setattr("requests.post", lambda *args, **kwargs: type('Response', (), {
            'status_code': 200,
            'get_json': mock_post_json
        })())
        
        # Test settings update
        render_cost_settings()
        
        # Verify settings were updated
        assert st.session_state.get('settings_changed', False)

    def test_cost_settings_validation(self, monkeypatch):
        """Test cost settings validation"""
        # Mock invalid settings
        invalid_settings = [
            CostSetting(
                id=str(uuid4()),
                type="fuel",
                category="variable",
                is_enabled=True,
                base_value=-1.0,  # Invalid negative value
                multiplier=0.0,    # Invalid zero multiplier
                currency="EUR",
                description="Invalid settings"
            )
        ]
        
        def mock_get_json(*args, **kwargs):
            return {"settings": [s.__dict__ for s in invalid_settings]}
        
        monkeypatch.setattr("requests.Response.get_json", mock_get_json)
        
        # Test validation
        with pytest.raises(ValueError):
            render_cost_settings()

    def test_cost_preview_calculation(self, monkeypatch):
        """Test cost preview functionality"""
        # Mock preview data
        preview_data = {
            "current_total": 1000.0,
            "projected_total": 1200.0,
            "breakdown": {
                "fuel": 500.0,
                "driver": 700.0
            },
            "warnings": ["Significant cost increase detected"]
        }
        
        def mock_preview_response(*args, **kwargs):
            return {"preview": preview_data}
        
        monkeypatch.setattr("requests.post", lambda *args, **kwargs: type('Response', (), {
            'status_code': 200,
            'get_json': mock_preview_response
        })())
        
        # Test preview calculation
        render_cost_settings()
        
        # Verify preview data
        assert st.session_state.get('preview_costs') is not None
        assert 'warnings' in st.session_state.get('preview_costs', {})

    def test_error_handling(self, monkeypatch):
        """Test error handling in cost settings"""
        # Mock API error
        def mock_api_error(*args, **kwargs):
            raise ConnectionError("API not available")
        
        monkeypatch.setattr("requests.get", mock_api_error)
        
        # Test error handling
        with pytest.raises(ConnectionError):
            render_cost_settings()

    def test_cost_component_timestamp_handling(self):
        test_timestamp = datetime.now(UTC)
        # Your test implementation for cost component timestamp handling