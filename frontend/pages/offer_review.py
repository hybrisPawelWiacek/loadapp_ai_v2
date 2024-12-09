import streamlit as st
import requests
from datetime import datetime
import pandas as pd
import plotly.express as px
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Constants
API_URL = "http://127.0.0.1:5000"
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

@dataclass
class OfferFilter:
    """Data class for offer filters."""
    start_date: datetime
    end_date: datetime
    min_price: float
    max_price: float
    limit: int
    offset: int

class OfferReviewPage:
    """Component for reviewing and analyzing offers."""
    
    def __init__(self):
        self.filters = self._initialize_filters()
        self.offers: Optional[List[Dict[str, Any]]] = None
        self.df: Optional[pd.DataFrame] = None
    
    def _initialize_filters(self) -> OfferFilter:
        """Initialize filter values from sidebar inputs."""
        st.sidebar.header("Filters")
        
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(datetime.now().date(), datetime.now().date()),
            key="date_range"
        )
        
        min_price = st.sidebar.number_input("Min Price (EUR)", value=0)
        max_price = st.sidebar.number_input("Max Price (EUR)", value=10000)
        
        # Pagination
        limit = st.sidebar.number_input("Items per page", min_value=1, value=10)
        page = st.sidebar.number_input("Page", min_value=1, value=1)
        offset = (page - 1) * limit
        
        return OfferFilter(
            start_date=date_range[0],
            end_date=date_range[1],
            min_price=min_price,
            max_price=max_price,
            limit=limit,
            offset=offset
        )
    
    def fetch_offers(self) -> bool:
        """
        Fetch offers based on current filters.
        Returns True if successful, False otherwise.
        """
        try:
            response = requests.get(
                f"{API_URL}/data/review",
                params={
                    "limit": self.filters.limit,
                    "offset": self.filters.offset,
                    "min_price": self.filters.min_price,
                    "max_price": self.filters.max_price,
                    "start_date": self.filters.start_date.isoformat(),
                    "end_date": self.filters.end_date.isoformat()
                },
                headers=HEADERS
            )
            
            if response.status_code == 200:
                self.offers = response.json()
                if self.offers:
                    self.df = pd.DataFrame(self.offers)
                    self.df['created_at'] = pd.to_datetime(self.df['created_at'])
                    self.df['date'] = self.df['created_at'].dt.date
                return True
            return False
        
        except Exception:
            return False
    
    def render_analytics(self) -> None:
        """Render analytics overview section."""
        if not self.df is not None or self.df.empty:
            return
        
        st.subheader("Analytics Overview")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_price = self.df['final_price'].mean()
            st.metric("Average Price", f"€{avg_price:.2f}")
        
        with col2:
            avg_margin = self.df['margin_percentage'].mean()
            st.metric("Average Margin", f"{avg_margin:.1f}%")
        
        with col3:
            total_offers = len(self.df)
            st.metric("Total Offers", total_offers)
        
        # Price Trend Chart
        st.subheader("Price Trends")
        fig = px.line(
            self.df,
            x='created_at',
            y='final_price',
            title='Offer Prices Over Time'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    def render_offer_details(self) -> None:
        """Render detailed offer information."""
        if not self.offers:
            return
        
        st.subheader("Offer Details")
        for offer in self.offers:
            self._render_offer_details(offer)
    
    def _render_offer_details(self, offer: Dict[str, Any]) -> None:
        """Render detailed information about a specific offer."""
        with st.expander(f"Offer Details - {offer['id']}", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### 📍 Route Details")
                st.markdown(f"**From:** {offer['route']['origin']['address']}")
                st.markdown(f"**To:** {offer['route']['destination']['address']}")
                st.markdown(f"**Distance:** {offer['route']['main_route']['distance_km']:.1f} km")
                st.markdown(f"**Empty Driving:** {offer['route']['empty_driving']['distance_km']:.1f} km")
            
            with col2:
                st.markdown("### ⏰ Schedule")
                st.markdown(f"**Pickup:** {offer['route']['pickup_time']}")
                st.markdown(f"**Delivery:** {offer['route']['delivery_time']}")
                st.markdown(f"**Total Duration:** {offer['route']['total_duration_hours']:.1f} hours")
                st.markdown(f"**Status:** {'✅ Feasible' if offer['route']['is_feasible'] else '❌ Not Feasible'}")
            
            with col3:
                st.markdown("### 💰 Cost & Pricing")
                st.metric("Base Cost", f"€{offer['costs']['total_cost']:.2f}")
                st.metric("Margin", f"{offer['margin']}%")
                st.metric("Final Price", f"€{offer['total_price']:.2f}")
            
            # Show cost breakdown
            st.markdown("### 📊 Cost Breakdown")
            breakdown_cols = st.columns(len(offer['costs']['breakdown']))
            for col, (cost_type, amount) in zip(breakdown_cols, offer['costs']['breakdown'].items()):
                with col:
                    st.metric(
                        cost_type.replace('_', ' ').title(),
                        f"€{amount:.2f}"
                    )
            
            # Show cargo details
            st.markdown("### 📦 Cargo Details")
            cargo_col1, cargo_col2 = st.columns(2)
            with cargo_col1:
                st.markdown(f"**Type:** {offer['route']['cargo']['type']}")
                st.markdown(f"**Transport Type:** {offer['route']['cargo']['transport_type']}")
                st.markdown(f"**Weight:** {offer['route']['cargo']['weight']} kg")
            with cargo_col2:
                st.markdown(f"**Value:** €{offer['route']['cargo']['value']:.2f}")
                if offer['route']['cargo'].get('special_requirements'):
                    st.markdown("**Special Requirements:**")
                    for req in offer['route']['cargo']['special_requirements']:
                        st.markdown(f"- {req}")
            
            # Show fun fact if available
            if 'fun_fact' in offer:
                st.info(f"🎯 Fun Fact: {offer['fun_fact']}")
    
    def render(self) -> None:
        """Render the complete offer review page."""
        st.title("📊 Offer Review")
        st.markdown("""
            Review and analyze past offers, including route details, costs, and AI insights.
        """)
        
        if not self.fetch_offers():
            st.error("Failed to load offers. Please try again.")
            return
        
        if not self.offers:
            st.info("No offers found matching your criteria.")
            return
        
        self.render_analytics()
        self.render_offer_details()

def render_offer_review_page() -> None:
    """Helper function to render the offer review page."""
    page = OfferReviewPage()
    page.render()
