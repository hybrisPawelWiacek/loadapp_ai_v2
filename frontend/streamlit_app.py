import streamlit as st
import requests
from datetime import datetime, timedelta
import json
import uuid
from components.route_input_form import render_route_input_form
from components.route_display import render_route_display, render_route_map
from components.advanced_cost_settings import render_cost_settings
from pages.offer_review import render_offer_review_page

# Constants
API_URL = "http://127.0.0.1:5000"
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# Configure the page
st.set_page_config(
    page_title="LoadApp.AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state initialization
if 'current_route' not in st.session_state:
    st.session_state.current_route = None
if 'current_costs' not in st.session_state:
    st.session_state.current_costs = None
if 'current_offer' not in st.session_state:
    st.session_state.current_offer = None
if 'step' not in st.session_state:
    st.session_state.step = None
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False
if 'margin' not in st.session_state:
    st.session_state.margin = 15

# Title and description
st.title("LoadApp.AI - Transport Planning Made Easy")
st.markdown("""
    Calculate routes, costs, and generate offers for your transport needs.
    Get AI-powered insights and fun facts about your routes!
""")

# Sidebar for navigation
page = st.sidebar.radio("Navigation", ["New Route", "Cost Settings", "Review Offers"])

if page == "New Route":
    # Step 1: Route Input Form
    form_data = render_route_input_form()
    
    if form_data:
        try:
            # Prepare request data
            pickup_datetime = datetime.combine(
                form_data['schedule']['pickup']['date'],
                form_data['schedule']['pickup']['time']
            ).isoformat()
            
            delivery_datetime = datetime.combine(
                form_data['schedule']['delivery']['date'],
                form_data['schedule']['delivery']['time']
            ).isoformat()
            
            # Send route calculation request
            request_data = {
                "origin": {
                    "latitude": form_data['origin']['coordinates']['lat'],
                    "longitude": form_data['origin']['coordinates']['lon'],
                    "address": form_data['origin']['address']
                },
                "destination": {
                    "latitude": form_data['destination']['coordinates']['lat'],
                    "longitude": form_data['destination']['coordinates']['lon'],
                    "address": form_data['destination']['address']
                },
                "pickup_time": pickup_datetime,
                "delivery_time": delivery_datetime,
                "cargo": {
                    "type": form_data['cargo']['transport_type'],
                    "weight": form_data['cargo'].get('weight', 1000),
                    "value": form_data['cargo'].get('value', 10000),
                    "special_requirements": []
                }
            }
            
            route_response = requests.post(
                f"{API_URL}/route",
                json=request_data,
                headers=HEADERS
            )
            
            if route_response.status_code == 200:
                st.session_state.current_route = route_response.json()
                st.session_state.current_costs = None  # Reset costs when new route is calculated
                st.session_state.step = 'route_summary'
                st.rerun()  # Force a rerun to update the UI
            else:
                st.error("Failed to calculate route. Please try again.")
        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    
    # Show route summary and calculate costs button if route exists
    if (hasattr(st.session_state, 'current_route') and 
        st.session_state.current_route is not None and 
        'main_route' in st.session_state.current_route):
        
        st.markdown("---")
        st.subheader("Route Summary")
        render_route_display(st.session_state.current_route)
        
        st.markdown("### Route Map")
        render_route_map(st.session_state.current_route)
        
        # Add Calculate Costs button if costs haven't been calculated yet
        if not st.session_state.current_costs:
            st.markdown("---")
            st.markdown("### Cost Calculation")
            if st.button("Calculate Costs", use_container_width=True, key="calc_costs_btn"):
                try:
                    cost_response = requests.post(
                        f"{API_URL}/costs/{st.session_state.current_route['id']}",
                        json={"route_id": st.session_state.current_route['id']},
                        headers=HEADERS
                    )
                    
                    if cost_response.status_code == 200:
                        st.session_state.current_costs = cost_response.json()
                        st.session_state.step = 'cost_summary'
                        st.rerun()
                    else:
                        st.error("Failed to calculate costs. Please try again.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
    
    # Show cost summary if costs exist
    if (hasattr(st.session_state, 'current_costs') and 
        st.session_state.current_costs is not None and 
        'breakdown' in st.session_state.current_costs):
        
        st.markdown("---")
        st.subheader("Cost Breakdown")
        
        costs = st.session_state.current_costs
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Base Cost", f"€{costs['breakdown']['base_cost']:.2f}")
        with col2:
            st.metric("Distance Cost", f"€{costs['breakdown']['distance_cost']:.2f}")
        with col3:
            st.metric("Time Cost", f"€{costs['breakdown']['time_cost']:.2f}")
        with col4:
            st.metric("Total Cost", f"€{costs['total_cost']:.2f}")
        
        # Show detailed breakdown in expander
        with st.expander("Detailed Cost Breakdown"):
            for cost_type, amount in costs['breakdown'].items():
                st.metric(f"{cost_type.replace('_', ' ').title()}", f"€{amount:.2f}")
        
        # Add margin input and generate offer button
        st.markdown("### Generate Offer")
        st.session_state.margin = st.slider("Profit Margin (%)", 
                                          min_value=5, 
                                          max_value=30, 
                                          value=st.session_state.margin, 
                                          step=1)
        
        if st.button("Generate Offer"):
            with st.spinner("Generating your offer... Did you know? AI-powered route optimization can reduce empty driving by up to 20%!"):
                try:
                    offer_response = requests.post(
                        f"{API_URL}/offer",
                        json={
                            "route_id": st.session_state.current_route['id'],
                            "margin": float(st.session_state.margin)
                        },
                        headers=HEADERS
                    )
                    
                    if offer_response.status_code in [200, 201]:
                        st.session_state.current_offer = offer_response.json()
                        st.session_state.step = 'offer_summary'
                    else:
                        st.error("Failed to generate offer. Please try again.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
    
    # Always show offer summary if it exists and has valid data
    if (hasattr(st.session_state, 'current_offer') and 
        st.session_state.current_offer is not None and 
        hasattr(st.session_state, 'current_costs') and 
        st.session_state.current_costs is not None):
        
        st.markdown("---")
        st.markdown("### 📋 Offer Summary")
        offer_col1, offer_col2, offer_col3 = st.columns(3)
        
        with offer_col1:
            st.metric("Base Cost", f"€{st.session_state.current_costs['total_cost']:.2f}")
        with offer_col2:
            st.metric("Margin", f"{st.session_state.margin}%")
        with offer_col3:
            final_price = st.session_state.current_costs['total_cost'] * (1 + st.session_state.margin/100)
            st.metric("Final Price", f"€{final_price:.2f}")
        
        # Display fun fact
        if 'fun_fact' in st.session_state.current_offer:
            st.info(f"🎯 Fun Fact: {st.session_state.current_offer['fun_fact']}")
        else:
            st.info("🎯 Fun Fact: Modern AI-powered logistics systems can reduce CO2 emissions by optimizing routes and reducing empty runs!")

elif page == "Cost Settings":
    render_cost_settings()

else:  # Review Offers
    render_offer_review_page()
