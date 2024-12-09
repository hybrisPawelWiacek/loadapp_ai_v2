import streamlit as st
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass

# Constants
API_URL = "http://127.0.0.1:5000"
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

@dataclass
class CostSetting:
    """Data class for cost setting item."""
    id: str
    type: str
    is_enabled: bool
    base_value: float
    multiplier: float

class AdvancedCostSettings:
    """Component for managing advanced cost settings."""
    
    def __init__(self):
        self.settings: List[CostSetting] = []
    
    def fetch_settings(self) -> bool:
        """
        Fetch current cost settings from the API.
        Returns True if successful, False otherwise.
        """
        try:
            response = requests.get(f"{API_URL}/costs/settings", headers=HEADERS)
            if response.status_code == 200:
                settings_data = response.json()
                self.settings = [
                    CostSetting(
                        id=item['id'],
                        type=item['type'],
                        is_enabled=item['is_enabled'],
                        base_value=float(item['base_value']),
                        multiplier=float(item.get('multiplier', 1.0))
                    )
                    for item in settings_data
                ]
                return True
            return False
        except Exception:
            return False
    
    def update_settings(self, updated_settings: List[Dict]) -> bool:
        """
        Update cost settings via API.
        Returns True if successful, False otherwise.
        """
        try:
            response = requests.post(
                f"{API_URL}/costs/settings",
                json=updated_settings,
                headers=HEADERS
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def render(self) -> None:
        """Render the advanced cost settings UI component."""
        st.subheader("Advanced Cost Settings")
        
        if not self.fetch_settings():
            st.error("Failed to fetch current cost settings. Please refresh the page.")
            return
        
        with st.form("advanced_cost_settings_form"):
            updated_settings = []
            
            # Create two columns for better layout
            col1, col2 = st.columns(2)
            
            # Split settings between columns
            for idx, item in enumerate(self.settings):
                # Alternate between columns
                with col1 if idx % 2 == 0 else col2:
                    container = self._render_setting_container(item)
                    updated_settings.append(container)
            
            # Submit button at the bottom
            if st.form_submit_button("Save Settings"):
                if self.update_settings(updated_settings):
                    st.success("Cost settings updated successfully!")
                else:
                    st.error("Failed to update cost settings. Please try again.")
    
    def _render_setting_container(self, item: CostSetting) -> Dict:
        """
        Render a container for a single cost setting.
        Returns the updated setting data.
        """
        st.markdown(f"### {item.type.title()}")
        
        with st.container():
            enabled = st.checkbox(
                "Enable this cost component",
                value=item.is_enabled,
                key=f"enabled_{item.id}"
            )
            
            base_value = st.number_input(
                "Base Cost Value",
                value=item.base_value,
                min_value=0.0,
                help="Base cost value for this component",
                key=f"base_{item.id}"
            )
            
            multiplier = st.number_input(
                "Cost Multiplier",
                value=item.multiplier,
                min_value=0.0,
                help="Multiplier applied to the base cost",
                key=f"multiplier_{item.id}"
            )
            
            return {
                "id": item.id,
                "type": item.type,
                "is_enabled": enabled,
                "base_value": base_value,
                "multiplier": multiplier
            }

def render_cost_settings() -> None:
    """Helper function to render the cost settings component."""
    settings = AdvancedCostSettings()
    settings.render()
