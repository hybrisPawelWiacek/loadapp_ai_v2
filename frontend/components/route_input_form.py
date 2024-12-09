import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

def render_route_input_form() -> Optional[Dict[str, Any]]:
    """
    Render the route input form component.
    Returns the form data if submitted, None otherwise.
    """
    with st.form("route_form"):
        st.subheader("Route Details")
        
        # Origin and Destination
        origin_data = _render_location_input("Origin", "Berlin, Germany", 52.5200, 13.4050)
        dest_data = _render_location_input("Destination", "Paris, France", 48.8566, 2.3522)
        
        # Schedule
        schedule_data = _render_schedule_input()
        
        # Cargo Details
        cargo_data = _render_cargo_input()
        
        # Submit button
        submitted = st.form_submit_button("Calculate Route")
        
        if submitted:
            return {
                "origin": origin_data,
                "destination": dest_data,
                "schedule": schedule_data,
                "cargo": cargo_data
            }
        return None

def _render_location_input(label: str, default_address: str, default_lat: float, default_lon: float) -> Dict[str, Any]:
    """Render location input fields with coordinates."""
    st.markdown(f"### {label}")
    
    address = st.text_input(
        "Address", 
        default_address,
        help=f"Enter the {label.lower()} address"
    )
    
    coords = st.expander("Advanced: Coordinates")
    with coords:
        lat = st.number_input("Latitude", value=default_lat)
        lon = st.number_input("Longitude", value=default_lon)
    
    return {
        "address": address,
        "coordinates": {"lat": lat, "lon": lon}
    }

def _render_schedule_input() -> Dict[str, Any]:
    """Render schedule input fields."""
    st.markdown("### Schedule")
    time_col1, time_col2 = st.columns(2)
    
    with time_col1:
        st.markdown("**Pickup**")
        pickup_date = st.date_input(
            "Date",
            datetime.now().date(),
            help="Select the pickup date"
        )
        pickup_time = st.time_input(
            "Time",
            datetime.now().replace(hour=9, minute=0),
            help="Select the pickup time"
        )
    
    with time_col2:
        st.markdown("**Delivery**")
        delivery_date = st.date_input(
            "Date",
            (datetime.now() + timedelta(days=1)).date(),
            help="Select the delivery date"
        )
        delivery_time = st.time_input(
            "Time",
            datetime.now().replace(hour=17, minute=0),
            help="Select the delivery time"
        )
    
    return {
        "pickup": {
            "date": pickup_date,
            "time": pickup_time
        },
        "delivery": {
            "date": delivery_date,
            "time": delivery_time
        }
    }

def _render_cargo_input() -> Dict[str, Any]:
    """Render cargo details input fields."""
    st.markdown("### Cargo Details")
    cargo_col1, cargo_col2, cargo_col3 = st.columns(3)
    
    with cargo_col1:
        cargo_type = st.selectbox(
            "Type",
            ["General", "Fragile", "Hazardous", "Refrigerated"],
            help="Select the type of cargo"
        )
        transport_type = st.selectbox(
            "Transport Type",
            ["Standard Truck", "Refrigerated Truck", "Heavy Load"],
            help="Select the required vehicle type"
        )
    
    with cargo_col2:
        cargo_weight = st.number_input(
            "Weight (kg)",
            min_value=0.0,
            value=1000.0,
            help="Enter the total weight of cargo"
        )
        cargo_volume = st.number_input(
            "Volume (m³)",
            min_value=0.0,
            value=10.0,
            help="Enter the total volume of cargo"
        )
    
    with cargo_col3:
        cargo_value = st.number_input(
            "Value (EUR)",
            min_value=0.0,
            value=5000.0,
            help="Enter the total value of cargo"
        )
        special_requirements = st.multiselect(
            "Special Requirements",
            ["Temperature Control", "Fragile Handling", "Express Delivery"],
            help="Select any special requirements"
        )
    
    return {
        "type": cargo_type,
        "transport_type": transport_type,
        "weight": cargo_weight,
        "volume": cargo_volume,
        "value": cargo_value,
        "special_requirements": special_requirements
    }
