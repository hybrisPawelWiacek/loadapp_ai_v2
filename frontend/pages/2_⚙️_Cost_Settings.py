import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# Constants
API_URL = "http://127.0.0.1:5000/api/v1"
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

st.set_page_config(
    page_title="LoadApp.AI - Cost Settings",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⚙️ Advanced Cost Settings")
st.markdown("""
    Manage and customize cost components for route calculations. Changes will affect all future cost calculations.
""")

# Initialize session state for settings
if 'settings_changed' not in st.session_state:
    st.session_state.settings_changed = False
if 'current_settings' not in st.session_state:
    st.session_state.current_settings = None

try:
    # Fetch current settings if not in session state
    if not st.session_state.current_settings:
        response = requests.get(f"{API_URL}/costs/settings", headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            st.session_state.current_settings = data['settings']
        else:
            st.error(f"Failed to load cost settings: {response.text}")
            st.stop()
    
    settings = st.session_state.current_settings
    
    # Create DataFrame for visualization
    df = pd.DataFrame(settings)
    
    # Analytics Section
    st.subheader("Cost Components Overview")
    
    # Bar chart of base values
    fig = px.bar(
        df,
        x='type',
        y='base_value',
        color='category',
        title='Base Values by Cost Type',
        labels={'type': 'Cost Type', 'base_value': 'Base Value (EUR)'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Settings Editor
    st.subheader("Edit Cost Settings")
    
    tabs = st.tabs(["Variable Costs", "Fixed Costs", "Special Costs"])
    
    with tabs[0]:  # Variable Costs
        st.write("Costs that vary with distance or time")
        variable_costs = [s for s in settings if s['category'] == 'variable']
        for cost in variable_costs:
            with st.expander(f"{cost['type'].title()} Settings"):
                cost['is_enabled'] = st.toggle(
                    "Enable this cost component",
                    value=cost['is_enabled'],
                    key=f"enable_{cost['id']}"
                )
                cost['base_value'] = st.number_input(
                    "Base Value (EUR)",
                    value=float(cost['base_value']),
                    key=f"base_{cost['id']}"
                )
                cost['multiplier'] = st.number_input(
                    "Multiplier",
                    value=float(cost['multiplier']),
                    min_value=0.0,
                    max_value=10.0,
                    key=f"mult_{cost['id']}"
                )
                st.write(f"Effective Rate: €{cost['base_value'] * cost['multiplier']:.2f}")
    
    with tabs[1]:  # Fixed Costs
        st.write("Costs that remain constant per trip")
        fixed_costs = [s for s in settings if s['category'] == 'fixed']
        for cost in fixed_costs:
            with st.expander(f"{cost['type'].title()} Settings"):
                cost['is_enabled'] = st.toggle(
                    "Enable this cost component",
                    value=cost['is_enabled'],
                    key=f"enable_{cost['id']}"
                )
                cost['base_value'] = st.number_input(
                    "Base Value (EUR)",
                    value=float(cost['base_value']),
                    key=f"base_{cost['id']}"
                )
                cost['multiplier'] = st.number_input(
                    "Multiplier",
                    value=float(cost['multiplier']),
                    min_value=0.0,
                    max_value=10.0,
                    key=f"mult_{cost['id']}"
                )
                st.write(f"Effective Rate: €{cost['base_value'] * cost['multiplier']:.2f}")
    
    with tabs[2]:  # Special Costs
        st.write("Special or conditional cost components")
        special_costs = [s for s in settings if s['category'] == 'special']
        for cost in special_costs:
            with st.expander(f"{cost['type'].title()} Settings"):
                cost['is_enabled'] = st.toggle(
                    "Enable this cost component",
                    value=cost['is_enabled'],
                    key=f"enable_{cost['id']}"
                )
                cost['base_value'] = st.number_input(
                    "Base Value (EUR)",
                    value=float(cost['base_value']),
                    key=f"base_{cost['id']}"
                )
                cost['multiplier'] = st.number_input(
                    "Multiplier",
                    value=float(cost['multiplier']),
                    min_value=0.0,
                    max_value=10.0,
                    key=f"mult_{cost['id']}"
                )
                st.write(f"Effective Rate: €{cost['base_value'] * cost['multiplier']:.2f}")
    
    # Save Changes
    if st.button("Save Changes", type="primary"):
        try:
            response = requests.post(
                f"{API_URL}/costs/settings",
                json={"cost_items": settings},
                headers=HEADERS
            )
            if response.status_code == 200:
                st.success("Settings saved successfully!")
                st.session_state.settings_changed = True
                st.session_state.current_settings = response.json()['settings']
            else:
                st.error(f"Failed to save settings: {response.text}")
        except Exception as e:
            st.error(f"Error saving settings: {str(e)}")
    
    # Reset Button
    if st.button("Reset to Defaults", type="secondary"):
        try:
            response = requests.post(
                f"{API_URL}/costs/settings/reset",
                headers=HEADERS
            )
            if response.status_code == 200:
                st.success("Settings reset to defaults!")
                st.session_state.current_settings = response.json()['settings']
                st.experimental_rerun()
            else:
                st.error(f"Failed to reset settings: {response.text}")
        except Exception as e:
            st.error(f"Error resetting settings: {str(e)}")
    
    # Warning about changes
    if st.session_state.settings_changed:
        st.warning(
            "⚠️ Cost settings have been modified. New calculations will use the updated values."
        )

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
