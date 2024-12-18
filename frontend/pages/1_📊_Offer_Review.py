import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from uuid import UUID
import json

# Constants
API_URL = "http://127.0.0.1:5001/api/v1"
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# Cost type categorization for better maintainability
COST_CATEGORIES = {
    'base': {
        'insurance': 'Insurance',
        'overhead': 'Overhead',
        'fixed': 'Fixed Costs'
    },
    'variable': {
        'fuel': 'Fuel',
        'driver': 'Driver',
        'maintenance': 'Maintenance',
        'time': 'Time-based',
        'toll': 'Toll'
    },
    'cargo': {
        'weight': 'Weight-based',
        'volume': 'Volume-based',
        'handling': 'Handling'
    }
}

MARKET_TYPES = {
    'origin': 'Origin Market',
    'transit': 'Transit Market',
    'destination': 'Destination Market'
}

INDICATOR_LABELS = {
    'demand': 'Market Demand',
    'supply': 'Supply Level',
    'competition': 'Competition',
    'seasonality': 'Seasonality',
    'price_trend': 'Price Trend'
}

@dataclass
class OfferFilter:
    """Data class for offer filters."""
    start_date: datetime
    end_date: datetime
    min_price: float
    max_price: float
    status: str
    currency: str
    countries: Optional[List[str]]
    regions: Optional[List[str]]
    client_id: Optional[UUID]
    page: int
    page_size: int
    include_settings: bool = True
    include_history: bool = True
    include_metrics: bool = True

def initialize_filters() -> OfferFilter:
    """Initialize enhanced filter values from sidebar."""
    st.sidebar.header("Filters")
    
    # Date range with default to last 30 days
    default_start = datetime.now() - timedelta(days=30)
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(default_start, datetime.now()),
        key="date_range"
    )
    
    # Price range
    col1, col2 = st.sidebar.columns(2)
    with col1:
        min_price = st.number_input("Min Price (EUR)", value=0.0, step=100.0)
    with col2:
        max_price = st.number_input("Max Price (EUR)", value=10000.0, step=100.0)
    
    # Additional filters
    status = st.sidebar.selectbox("Status", ["all", "pending", "accepted", "rejected"])
    currency = st.sidebar.selectbox("Currency", ["EUR", "USD", "GBP"])
    
    # Advanced filters in expander
    with st.sidebar.expander("Advanced Filters"):
        countries = st.multiselect("Countries", ["Germany", "France", "Italy", "Spain"])
        regions = st.multiselect("Regions", ["North", "South", "East", "West"])
        
    # Pagination
    page_size = st.sidebar.number_input("Items per page", min_value=1, value=10)
    page = st.sidebar.number_input("Page", min_value=1, value=1)
    
    return OfferFilter(
        start_date=date_range[0],
        end_date=date_range[1],
        min_price=min_price,
        max_price=max_price,
        status=status,
        currency=currency,
        countries=countries,
        regions=regions,
        client_id=None,
        page=page,
        page_size=page_size
    )

def fetch_offers(filters: OfferFilter) -> tuple[List[Dict[str, Any]], int]:
    """Fetch offers based on filters."""
    params = {
        "page_size": filters.page_size,
        "page": filters.page,
        "min_price": filters.min_price,
        "max_price": filters.max_price,
        "start_date": filters.start_date.strftime("%Y-%m-%d"),
        "end_date": filters.end_date.strftime("%Y-%m-%d"),
        "status": filters.status if filters.status != "all" else None,
        "currency": filters.currency,
        "countries": json.dumps(filters.countries) if filters.countries else None,
        "regions": json.dumps(filters.regions) if filters.regions else None,
        "include_settings": "true" if filters.include_settings else "false",
        "include_history": "true" if filters.include_history else "false",
        "include_metrics": "true" if filters.include_metrics else "false"
    }
    
    response = requests.get(
        f"{API_URL}/offers",
        params={k: v for k, v in params.items() if v is not None},
        headers=HEADERS
    )
    
    if response.status_code != 200:
        st.error(f"Error fetching offers: {response.json()}")
        return [], 0
        
    data = response.json()
    return data.get("offers", []), data.get("total", 0)

def display_analytics(df: pd.DataFrame):
    """Display analytics overview."""
    st.subheader("Analytics Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        avg_price = df['final_price'].mean()
        st.metric("Average Price", f"€{avg_price:.2f}")
    with col2:
        avg_margin = df['margin_percentage'].mean()
        st.metric("Average Margin", f"{avg_margin:.1f}%")
    with col3:
        total_offers = len(df)
        st.metric("Total Offers", total_offers)
    with col4:
        success_rate = (df['status'] == 'accepted').mean() * 100
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    # Price Trend Chart
    st.subheader("Price Trends")
    fig = px.line(
        df,
        x='created_at',
        y='final_price',
        title='Offer Prices Over Time'
    )
    st.plotly_chart(fig, use_container_width=True)

def display_offer_details(offer: Dict[str, Any]):
    """Display detailed offer information."""
    tabs = st.tabs(["Overview", "Route Details", "Cost Breakdown", "Market Analysis"])
    
    with tabs[0]:  # Overview
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Pricing**")
            st.write(f"Base Price: €{offer['base_price']:.2f}")
            st.write(f"Margin: {offer['margin_percentage']}%")
            st.write(f"Final Price: €{offer['final_price']:.2f}")
        with col2:
            st.write("**Status**")
            st.write(f"Created: {offer['created_at']}")
            st.write(f"Status: {offer['status'].title()}")
    
    with tabs[1]:  # Route Details
        try:
            route_response = requests.get(
                f"{API_URL}/route/{offer['route_id']}",
                headers=HEADERS
            )
            if route_response.status_code == 200:
                route = route_response.json()
                
                # Display map
                if 'coordinates' in route:
                    m = folium.Map(location=route['coordinates'][0], zoom_start=6)
                    points = route['coordinates']
                    folium.PolyLine(points, weight=2, color='blue', opacity=0.8).add_to(m)
                    st_folium(m, height=400)
                
                # Route information
                st.write("**Route Information**")
                st.write(f"Origin: {route['origin']['address']}")
                st.write(f"Destination: {route['destination']['address']}")
                st.write(f"Total Duration: {route['total_duration_hours']} hours")
                
                # Timeline
                st.write("**Timeline**")
                for event in route['timeline']:
                    st.write(
                        f"- {event['event_type'].title()}: "
                        f"{event['planned_time']} at {event['location']['address']}"
                    )
            else:
                st.warning("Route details not available")
        except Exception as e:
            st.error(f"Error loading route details: {str(e)}")
    
    with tabs[2]:  # Cost Breakdown
        st.write("**Cost Components**")
        
        # Group costs by category
        for category, subcategories in COST_CATEGORIES.items():
            st.write(f"**{category.title()} Costs**")
            for cost_type, label in subcategories.items():
                if cost_type in offer['cost_breakdown']:
                    st.write(f"- {label}: €{offer['cost_breakdown'][cost_type]:.2f}")
        
        st.write(f"**Total Cost: €{offer['cost_breakdown'].get('total', 0):.2f}**")
    
    with tabs[3]:  # Market Analysis
        if 'market_analysis' in offer:
            for market_type, market_label in MARKET_TYPES.items():
                if market_type in offer['market_analysis']:
                    st.write(f"**{market_label}**")
                    market_data = offer['market_analysis'][market_type]
                    for indicator, label in INDICATOR_LABELS.items():
                        if indicator in market_data:
                            st.write(f"- {label}: {market_data[indicator]}")

def main():
    st.set_page_config(
        page_title="LoadApp.AI - Offer Review",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("📊 Offer Review")
    st.markdown("""
        Review and analyze past offers, including route details, costs, and market insights.
    """)

    # Initialize filters
    filters = initialize_filters()
    
    try:
        # Fetch offers
        offers, total_offers = fetch_offers(filters)
        
        if not offers:
            st.info("No offers found matching your criteria.")
            return
            
        # Create DataFrame for analytics
        df = pd.DataFrame(offers)
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['date'] = df['created_at'].dt.date
        
        # Display analytics
        display_analytics(df)
        
        # Offer List
        st.subheader("Offer Details")
        for offer in offers:
            with st.expander(
                f"Offer {offer['id']} - {offer['created_at']} - €{offer['final_price']:.2f}"
            ):
                display_offer_details(offer)
        
        # Pagination controls
        st.write("---")
        col1, col2 = st.columns(2)
        with col1:
            if filters.page > 1:
                if st.button("← Previous Page"):
                    st.session_state.page = filters.page - 1
                    st.experimental_rerun()
        with col2:
            if len(offers) == filters.page_size:
                if st.button("Next Page →"):
                    st.session_state.page = filters.page + 1
                    st.experimental_rerun()
                    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
