import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import json

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

try:
    # Fetch current settings
    response = requests.get(f"{API_URL}/costs/settings", headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        settings = data['settings']
        
        # Create DataFrame for visualization
        df = pd.DataFrame([{
            'type': s['type'],
            'category': s['category'],
            'base_value': float(s.get('base_value', 0.0)),
            'name': s['name']
        } for s in settings])
        
        # Analytics Section
        st.subheader("Cost Components Overview")
        
        # Bar chart of base values
        if not df.empty:
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
        
        # Create tabs for different cost categories
        tab_variable, tab_fixed, tab_special = st.tabs([
            "Variable Costs (Distance/Time)",
            "Fixed Costs (Base)",
            "Special Costs (Cargo)"
        ])
        
        # Variable Costs Tab
        with tab_variable:
            st.write("Costs that vary with distance or time")
            for cost in [s for s in settings if s['category'] == 'variable']:
                with st.expander(f"{cost['type'].title()} Settings", expanded=True):
                    # Enable/Disable toggle
                    cost['is_enabled'] = st.toggle(
                        "Enable this cost component",
                        value=cost.get('is_enabled', True),
                        key=f"enable_{cost['id']}"
                    )
                    
                    # Base value input
                    min_value = 0.1 if cost['type'] == 'fuel' else (
                        1.0 if cost['type'] == 'time' else (
                        0.05 if cost['type'] == 'maintenance' else 0.01
                    ))
                    
                    cost['base_value'] = st.number_input(
                        "Base Value (EUR)",
                        min_value=min_value,
                        value=max(float(cost.get('base_value', min_value)), min_value),
                        step=min_value,
                        format="%.3f",
                        help=f"Minimum value: €{min_value:.3f}",
                        key=f"base_{cost['id']}"
                    )
                    
                    # Multiplier input
                    cost['multiplier'] = st.number_input(
                        "Multiplier",
                        min_value=0.0,
                        max_value=10.0,
                        value=float(cost.get('multiplier', 1.0)),
                        step=0.1,
                        format="%.2f",
                        key=f"mult_{cost['id']}"
                    )
                    
                    st.write(f"Effective Rate: €{cost['base_value'] * cost['multiplier']:.3f}")
                    if cost.get('description'):
                        st.caption(cost['description'])
        
        # Fixed Costs Tab
        with tab_fixed:
            st.write("Costs that remain constant per trip")
            for cost in [s for s in settings if s['category'] == 'base']:
                with st.expander(f"{cost['type'].title()} Settings", expanded=True):
                    cost['is_enabled'] = st.toggle(
                        "Enable this cost component",
                        value=cost.get('is_enabled', True),
                        key=f"enable_{cost['id']}"
                    )
                    
                    min_value = 0.01  # Base minimum value for fixed costs
                    cost['base_value'] = st.number_input(
                        "Base Value (EUR)",
                        min_value=min_value,
                        value=max(float(cost.get('base_value', min_value)), min_value),
                        step=min_value,
                        format="%.3f",
                        help=f"Minimum value: €{min_value:.3f}",
                        key=f"base_{cost['id']}"
                    )
                    
                    cost['multiplier'] = st.number_input(
                        "Multiplier",
                        min_value=0.0,
                        max_value=10.0,
                        value=float(cost.get('multiplier', 1.0)),
                        step=0.1,
                        format="%.2f",
                        key=f"mult_{cost['id']}"
                    )
                    
                    st.write(f"Effective Rate: €{cost['base_value'] * cost['multiplier']:.3f}")
                    if cost.get('description'):
                        st.caption(cost['description'])
        
        # Special Costs Tab
        with tab_special:
            st.write("Special or conditional cost components")
            for cost in [s for s in settings if s['category'] == 'cargo-specific']:
                with st.expander(f"{cost['type'].title()} Settings", expanded=True):
                    cost['is_enabled'] = st.toggle(
                        "Enable this cost component",
                        value=cost.get('is_enabled', True),
                        key=f"enable_{cost['id']}"
                    )
                    
                    min_value = 0.01 if cost['type'] == 'weight' else 0.01
                    cost['base_value'] = st.number_input(
                        "Base Value (EUR)",
                        min_value=min_value,
                        value=max(float(cost.get('base_value', min_value)), min_value),
                        step=min_value,
                        format="%.3f",
                        help=f"Minimum value: €{min_value:.3f}",
                        key=f"base_{cost['id']}"
                    )
                    
                    cost['multiplier'] = st.number_input(
                        "Multiplier",
                        min_value=0.0,
                        max_value=10.0,
                        value=float(cost.get('multiplier', 1.0)),
                        step=0.1,
                        format="%.2f",
                        key=f"mult_{cost['id']}"
                    )
                    
                    st.write(f"Effective Rate: €{cost['base_value'] * cost['multiplier']:.3f}")
                    if cost.get('description'):
                        st.caption(cost['description'])
        
        # Save and Reset buttons
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("Save Changes", type="primary", use_container_width=True):
                try:
                    updated_settings = []
                    for item in settings:
                        updated_settings.append({
                            "id": item['id'],
                            "name": item['name'],
                            "type": item['type'],
                            "category": item['category'],
                            "is_enabled": item['is_enabled'],
                            "value": item['base_value'],
                            "multiplier": item['multiplier'],
                            "currency": item.get('currency', 'EUR'),
                            "description": item.get('description', '')
                        })
                    
                    response = requests.post(
                        f"{API_URL}/costs/settings",
                        json=updated_settings,
                        headers=HEADERS
                    )
                    
                    if response.status_code == 200:
                        st.success("Settings saved successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to save settings: {response.text}")
                except Exception as e:
                    st.error(f"Error saving settings: {str(e)}")
        
        with col2:
            if st.button("Reset to Defaults", type="secondary", use_container_width=True):
                try:
                    response = requests.post(
                        f"{API_URL}/costs/settings/reset",
                        headers=HEADERS
                    )
                    if response.status_code == 200:
                        st.success("Settings reset to defaults!")
                        st.rerun()
                    else:
                        st.error(f"Failed to reset settings: {response.text}")
                except Exception as e:
                    st.error(f"Error resetting settings: {str(e)}")

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
