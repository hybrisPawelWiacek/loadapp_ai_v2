import streamlit as st
from typing import Dict, Any, List
from datetime import datetime

def render_route_display(route_data: Dict[str, Any]) -> None:
    """
    Render the route display component showing route details and timeline.
    
    Args:
        route_data: Dictionary containing route information including timeline events
    """
    st.markdown("---")
    # Basic route information
    col1, col2, col3 = st.columns(3)
    with col1:
        total_distance = route_data['main_route']['distance_km'] + route_data['empty_driving']['distance_km']
        st.metric("Total Distance", f"{total_distance:.1f} km")
    with col2:
        st.metric("Duration", f"{route_data['total_duration_hours']:.1f} hours")
    with col3:
        st.metric("Empty Driving", f"{route_data['empty_driving']['distance_km']:.1f} km")
    
    # Timeline visualization
    st.markdown("### Route Timeline")
    _render_timeline(route_data['timeline'])
    
    # Additional route details
    with st.expander("Detailed Route Information"):
        _render_detailed_info(route_data)

def _render_timeline(timeline: List[Dict[str, Any]]) -> None:
    """Render the route timeline with events."""
    for idx, event in enumerate(timeline):
        col1, col2, col3 = st.columns([1, 3, 2])
        
        with col1:
            st.markdown(f"**{event['type'].title()}**")
        
        with col2:
            st.markdown(f"{event['location']['address']}")
            if event.get('description'):
                st.caption(event['description'])
        
        with col3:
            planned_time = datetime.fromisoformat(event['time'])
            st.markdown(planned_time.strftime("%Y-%m-%d %H:%M"))
            if event.get('duration_minutes'):
                st.caption(f"Duration: {event['duration_minutes']} min")
        
        # Add visual separator between events
        if idx < len(timeline) - 1:
            st.markdown("↓")

def _render_detailed_info(route_data: Dict[str, Any]) -> None:
    """Render detailed route information."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Route Details")
        st.markdown(f"- **Origin:** {route_data['origin']['address']}")
        st.markdown(f"- **Destination:** {route_data['destination']['address']}")
        st.markdown(f"- **Pickup Time:** {route_data['pickup_time']}")
        st.markdown(f"- **Delivery Time:** {route_data['delivery_time']}")
    
    with col2:
        st.markdown("#### Additional Information")
        st.markdown(f"- **Route ID:** {route_data['id']}")
        st.markdown(f"- **Feasibility:** {'✅ Feasible' if route_data['is_feasible'] else '❌ Not Feasible'}")
        st.markdown(f"- **Duration Validation:** {'✅ Valid' if route_data['duration_validation'] else '❌ Invalid'}")

def render_route_map(route_data: Dict[str, Any]) -> None:
    """
    Render a map visualization of the route.
    This is a placeholder for future map integration.
    
    Args:
        route_data: Dictionary containing route coordinates and waypoints
    """
    st.info("Map visualization will be implemented in future versions.")
