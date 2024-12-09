import streamlit as st
import requests
from typing import Dict, List

# Constants
API_URL = "http://127.0.0.1:5000"
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def render_cost_settings():
    """Render the advanced cost settings UI component."""
    st.subheader("Advanced Cost Settings")
    
    try:
        # Fetch current settings
        response = requests.get(f"{API_URL}/costs/settings", headers=HEADERS)
        if response.status_code == 200:
            settings = response.json()
            
            # Create a form for settings
            with st.form("advanced_cost_settings_form"):
                updated_settings = []
                
                # Create two columns for better layout
                col1, col2 = st.columns(2)
                
                # Split settings between columns
                for idx, item in enumerate(settings):
                    # Alternate between columns
                    with col1 if idx % 2 == 0 else col2:
                        st.markdown(f"### {item['type'].title()}")
                        
                        # Create a container for each setting
                        with st.container():
                            enabled = st.checkbox(
                                "Enable this cost component", 
                                value=item['is_enabled'],
                                key=f"enabled_{item['id']}"
                            )
                            
                            base_value = st.number_input(
                                "Base Cost Value",
                                value=float(item['base_value']),
                                min_value=0.0,
                                help="Base cost value for this component",
                                key=f"base_{item['id']}"
                            )
                            
                            multiplier = st.number_input(
                                "Cost Multiplier",
                                value=float(item.get('multiplier', 1.0)),
                                min_value=0.0,
                                help="Multiplier applied to the base cost",
                                key=f"multiplier_{item['id']}"
                            )
                            
                            # Add setting to the update list
                            updated_settings.append({
                                "id": item['id'],
                                "type": item['type'],
                                "is_enabled": enabled,
                                "base_value": base_value,
                                "multiplier": multiplier
                            })
                
                # Submit button at the bottom
                if st.form_submit_button("Save Settings"):
                    # Send update request
                    update_response = requests.post(
                        f"{API_URL}/costs/settings",
                        json=updated_settings,
                        headers=HEADERS
                    )
                    
                    if update_response.status_code == 200:
                        st.success("Cost settings updated successfully!")
                    else:
                        st.error("Failed to update cost settings. Please try again.")
        
        else:
            st.error("Failed to fetch current cost settings. Please refresh the page.")
    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
