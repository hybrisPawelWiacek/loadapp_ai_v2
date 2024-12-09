import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import folium
from streamlit_folium import folium_static
import json
from uuid import UUID

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
    status: str
    currency: str
    countries: Optional[List[str]]
    regions: Optional[List[str]]
    client_id: Optional[UUID]
    page: int
    page_size: int
    include_settings: bool
    include_history: bool
    include_metrics: bool

class OfferReviewPage:
    """Enhanced component for reviewing and analyzing offers."""
    
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

    def __init__(self):
        """Initialize the OfferReviewPage component."""
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.filters = self._initialize_filters()
        self.offers: Optional[List[Dict[str, Any]]] = None
        self.total_offers: int = 0
        self.df: Optional[pd.DataFrame] = None
        self.selected_offer: Optional[Dict[str, Any]] = None
        
    def _initialize_filters(self) -> OfferFilter:
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
        price_range = st.sidebar.slider(
            "Price Range",
            min_value=0,
            max_value=10000,
            value=(0, 10000),
            step=100,
            key="price_range"
        )
        
        # Status and currency
        status = st.sidebar.selectbox(
            "Status",
            ["All"] + ["DRAFT", "PENDING", "SENT", "ACCEPTED", "REJECTED", "EXPIRED"],
            key="status"
        )
        
        currency = st.sidebar.selectbox(
            "Currency",
            ["EUR", "USD", "GBP"],
            key="currency"
        )
        
        # Geographic filters
        countries = st.sidebar.multiselect(
            "Countries",
            ["Germany", "France", "Spain", "Italy", "Netherlands"],
            key="countries"
        )
        
        regions = st.sidebar.multiselect(
            "Regions",
            ["Western Europe", "Eastern Europe", "Nordic", "Mediterranean"],
            key="regions"
        )
        
        # Client filter
        client_id = st.sidebar.text_input(
            "Client ID",
            key="client_id"
        )
        
        # Pagination
        page = st.sidebar.number_input(
            "Page",
            min_value=1,
            value=1,
            key="page"
        )
        
        page_size = st.sidebar.selectbox(
            "Items per page",
            [10, 20, 50, 100],
            key="page_size"
        )
        
        # Include options
        include_settings = st.sidebar.checkbox(
            "Include Settings",
            value=False,
            key="include_settings"
        )
        
        include_history = st.sidebar.checkbox(
            "Include Version History",
            value=False,
            key="include_history"
        )
        
        include_metrics = st.sidebar.checkbox(
            "Include Metrics",
            value=False,
            key="include_metrics"
        )
        
        return OfferFilter(
            start_date=date_range[0],
            end_date=date_range[1],
            min_price=price_range[0],
            max_price=price_range[1],
            status=None if status == "All" else status,
            currency=currency,
            countries=countries if countries else None,
            regions=regions if regions else None,
            client_id=UUID(client_id) if client_id else None,
            page=page,
            page_size=page_size,
            include_settings=include_settings,
            include_history=include_history,
            include_metrics=include_metrics
        )

    def fetch_offers(self) -> None:
        """Fetch offers with enhanced filtering."""
        try:
            response = requests.get(
                f"{API_URL}/offers",
                headers=HEADERS,
                params={
                    "start_date": self.filters.start_date.isoformat(),
                    "end_date": self.filters.end_date.isoformat(),
                    "min_price": self.filters.min_price,
                    "max_price": self.filters.max_price,
                    "status": self.filters.status,
                    "currency": self.filters.currency,
                    "countries": json.dumps(self.filters.countries) if self.filters.countries else None,
                    "regions": json.dumps(self.filters.regions) if self.filters.regions else None,
                    "client_id": str(self.filters.client_id) if self.filters.client_id else None,
                    "page": self.filters.page,
                    "page_size": self.filters.page_size,
                    "include_settings": self.filters.include_settings,
                    "include_history": self.filters.include_history,
                    "include_metrics": self.filters.include_metrics
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.offers = data["offers"]
                self.total_offers = data["total"]
                self.df = pd.DataFrame(self.offers)
            else:
                st.error(f"Failed to fetch offers: {response.text}")
                
        except Exception as e:
            st.error(f"Error fetching offers: {str(e)}")

    def calculate_costs(self, route_id: str) -> bool:
        """Calculate costs for a route and refresh offer data."""
        try:
            response = requests.post(
                f"{API_URL}/api/v1/costs/{route_id}",
                headers=HEADERS
            )
            
            if response.status_code == 200:
                # Store the cost data directly
                cost_data = response.json()
                
                # Update the selected offer with new cost data
                if self.selected_offer and 'route' in self.selected_offer:
                    self.selected_offer['cost_breakdown'] = cost_data.get('cost_breakdown')
                    self.selected_offer['total_cost'] = cost_data.get('total_cost')
                    self.selected_offer['currency'] = cost_data.get('currency')
                
                # Refresh the full offer list
                self.fetch_offers()
                return True
            else:
                st.error(f"Failed to calculate costs: {response.text}")
                return False
                
        except Exception as e:
            st.error(f"Error calculating costs: {str(e)}")
            return False

    def render_offer_details(self, offer: Dict[str, Any]) -> None:
        """Render comprehensive offer details in tabs."""
        tabs = st.tabs([
            "Basic Info",
            "Cost Analysis",
            "AI Insights",
            "Route Details",
            "History",
            "Metrics",
            "Applied Settings",
            "Market Insights"
        ])
        
        with tabs[0]:
            self._render_basic_info(offer)
            
        with tabs[1]:
            self._render_cost_analysis(offer)
            
        with tabs[2]:
            self._render_ai_insights(offer)
            
        with tabs[3]:
            self._render_route_details(offer)
            
        with tabs[4]:
            self._render_history(offer)
            
        with tabs[5]:
            self._render_metrics(offer)
            
        with tabs[6]:
            self._render_applied_settings(offer)
            
        with tabs[7]:
            self._render_market_insights(offer)

    def _render_basic_info(self, offer: Dict[str, Any]) -> None:
        """Render basic offer information."""
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### Offer Details")
            st.write(f"**ID:** {offer['id']}")
            st.write(f"**Status:** {offer['status']}")
            st.write(f"**Created:** {offer['created_at']}")
            st.write(f"**Updated:** {offer['updated_at']}")
            st.write(f"**Version:** {offer['version']}")
            
        with col2:
            st.write("### Client Information")
            st.write(f"**Client ID:** {offer.get('client_id', 'N/A')}")
            st.write(f"**Client Name:** {offer.get('client_name', 'N/A')}")
            st.write(f"**Client Contact:** {offer.get('client_contact', 'N/A')}")

    def _render_cost_analysis(self, offer: Dict[str, Any]) -> None:
        """Render detailed cost analysis with visualizations."""
        st.write("### Cost Breakdown")
        
        # Add Calculate Costs button
        route_id = offer.get('route', {}).get('id')
        if route_id:
            if st.button("Calculate Costs", key=f"calc_costs_{route_id}"):
                with st.spinner("Calculating costs..."):
                    if self.calculate_costs(route_id):
                        # Refresh the selected offer data after calculation
                        self.selected_offer = next(
                            (o for o in self.offers if o['id'] == offer['id']),
                            None
                        )
                        if self.selected_offer:
                            offer = self.selected_offer
                        st.success("Costs calculated successfully!")
                    else:
                        st.error("Failed to calculate costs")
        
        cost_breakdown = offer.get('cost_breakdown')
        if not cost_breakdown:
            st.info("No cost information available. Click 'Calculate Costs' to generate cost breakdown.")
            return

        # Get the total cost from the offer
        total_cost = offer.get('total_cost', 0.0)
        currency = offer.get('currency', 'EUR')

        # Create columns for different cost categories
        col1, col2, col3 = st.columns(3)

        # Display base costs
        with col1:
            st.write("#### Base Costs")
            base_costs = cost_breakdown.get('base_costs', {})
            for cost_type, amount in base_costs.items():
                if amount > 0:  # Only show non-zero costs
                    display_name = self.COST_CATEGORIES['base'].get(cost_type, cost_type.title())
                    st.write(f"**{display_name}:** {amount:.2f} {currency}")

        # Display variable costs
        with col2:
            st.write("#### Variable Costs")
            variable_costs = cost_breakdown.get('variable_costs', {})
            for cost_type, amount in variable_costs.items():
                if amount > 0:  # Only show non-zero costs
                    display_name = self.COST_CATEGORIES['variable'].get(cost_type, cost_type.title())
                    st.write(f"**{display_name}:** {amount:.2f} {currency}")

        # Display cargo-specific costs
        with col3:
            st.write("#### Cargo-Specific Costs")
            cargo_costs = cost_breakdown.get('cargo_specific_costs', {})
            for cargo_id, costs in cargo_costs.items():
                cargo_type = offer.get('route', {}).get('cargo', {}).get('type', 'Unknown Cargo')
                for cost_type, amount in costs.items():
                    if amount > 0:  # Only show non-zero costs
                        display_name = self.COST_CATEGORIES['cargo'].get(cost_type, cost_type.title())
                        st.write(f"**{display_name} ({cargo_type}):** {amount:.2f} {currency}")

        # Display total cost
        st.write("---")
        st.write(f"### Total Cost: {total_cost:.2f} {currency}")

        # Create a pie chart of costs
        cost_data = []
        
        # Add base costs to chart data
        for cost_type, amount in base_costs.items():
            if amount > 0:
                display_name = self.COST_CATEGORIES['base'].get(cost_type, cost_type.title())
                cost_data.append({'Category': display_name, 'Amount': amount})
        
        # Add variable costs to chart data
        for cost_type, amount in variable_costs.items():
            if amount > 0:
                display_name = self.COST_CATEGORIES['variable'].get(cost_type, cost_type.title())
                cost_data.append({'Category': display_name, 'Amount': amount})
        
        # Add cargo-specific costs to chart data
        for cargo_id, costs in cargo_costs.items():
            cargo_type = offer.get('route', {}).get('cargo', {}).get('type', 'Unknown Cargo')
            for cost_type, amount in costs.items():
                if amount > 0:
                    display_name = f"{self.COST_CATEGORIES['cargo'].get(cost_type, cost_type.title())} ({cargo_type})"
                    cost_data.append({'Category': display_name, 'Amount': amount})

        if cost_data:
            df = pd.DataFrame(cost_data)
            fig = px.pie(df, values='Amount', names='Category', title='Cost Distribution')
            st.plotly_chart(fig)

    def _render_ai_insights(self, offer: Dict[str, Any]) -> None:
        """Render AI insights with visualizations."""
        st.write("### AI Insights")
        
        insights = offer.get('ai_insights', {})
        if not insights:
            st.info("No AI insights available for this offer")
            return
        
        # Display fun facts if available
        fun_facts = insights.get('fun_facts', [])
        if fun_facts:
            st.write("#### Fun Facts About Your Transport Route")
            for fact in fun_facts:
                st.info(fact)
        
        # Confidence score gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=insights.get('confidence_score', 0) * 100,
            title={'text': "AI Confidence Score"},
            gauge={'axis': {'range': [0, 100]}}
        ))
        
        st.plotly_chart(fig)
        
        # Other insights
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Route Complexity:**", insights.get('route_complexity', 'N/A'))
            st.write("**Market Position:**", insights.get('market_position', 'N/A'))
        with col2:
            st.write("**Cost Efficiency:**", f"{insights.get('cost_efficiency', 0):.2f}")
            st.write("**Risk Score:**", insights.get('risk_score', 'N/A'))

    def _render_route_details(self, offer: Dict[str, Any]) -> None:
        """Render route details with map."""
        st.write("### Route Information")
        
        if 'route' in offer:
            route = offer['route']
            
            # Create map
            m = folium.Map(location=[0, 0], zoom_start=4)
            
            # Add markers and path
            points = []
            if 'origin' in route:
                origin = route['origin']
                folium.Marker(
                    [origin['lat'], origin['lng']],
                    popup='Origin',
                    icon=folium.Icon(color='green')
                ).add_to(m)
                points.append([origin['lat'], origin['lng']])
            
            if 'destination' in route:
                dest = route['destination']
                folium.Marker(
                    [dest['lat'], dest['lng']],
                    popup='Destination',
                    icon=folium.Icon(color='red')
                ).add_to(m)
                points.append([dest['lat'], dest['lng']])
            
            if points:
                folium.PolyLine(points, weight=2, color='blue').add_to(m)
                m.fit_bounds(points)
            
            folium_static(m)
            
            # Route details
            st.write(f"**Distance:** {route.get('distance_km', 'N/A')} km")
            st.write(f"**Duration:** {route.get('duration_hours', 'N/A')} hours")
            
            # Add Calculate Costs button if costs haven't been calculated
            if not offer.get('cost_breakdown'):
                if st.button("Calculate Costs"):
                    with st.spinner("Calculating costs..."):
                        if self.calculate_costs(str(route['id'])):
                            st.success("Costs calculated successfully!")
                            st.experimental_rerun()
        else:
            st.info("No route information available")

    def _render_history(self, offer: Dict[str, Any]) -> None:
        """Render version history."""
        st.write("### Version History")
        
        if not offer.get('_version_history'):
            st.info("No version history available")
            return
        
        for version in offer['_version_history']:
            with st.expander(f"Version {version['version']} - {version['changed_at']}"):
                st.write(f"**Changed By:** {version['changed_by']}")
                st.write(f"**Reason:** {version['reason']}")
                st.write("**Changes:**")
                st.json(version['changes'])

    def _render_metrics(self, offer: Dict[str, Any]) -> None:
        """Render offer metrics with visualizations."""
        st.write("### Offer Metrics")
        
        metrics = offer.get('_metrics')
        if not metrics:
            st.info("No metrics available")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Processing time gauge
            fig1 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=metrics['processing_time_ms'],
                title={'text': "Processing Time (ms)"},
                gauge={'axis': {'range': [0, 1000]}}
            ))
            st.plotly_chart(fig1)
        
        with col2:
            # AI confidence gauge
            fig2 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=metrics['ai_confidence_score'] * 100,
                title={'text': "AI Confidence Score"},
                gauge={'axis': {'range': [0, 100]}}
            ))
            st.plotly_chart(fig2)
        
        # Additional metrics
        st.write("### Additional Metrics")
        for key, value in metrics.get('metadata', {}).items():
            st.write(f"**{key.replace('_', ' ').title()}:** {value}")

    def _render_applied_settings(self, offer: Dict[str, Any]) -> None:
        """Render applied settings."""
        st.write("### Applied Settings")
        
        settings = offer.get('applied_settings')
        if not settings:
            st.info("No settings information available")
            return
        
        # Display settings in an organized way
        for category, values in settings.items():
            with st.expander(category.replace('_', ' ').title()):
                if isinstance(values, dict):
                    for key, value in values.items():
                        st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                else:
                    st.write(str(values))

    def _render_market_insights(self, offer_data: Dict[str, Any]):
        """Render market insights section with visualizations."""
        st.subheader("Market Insights Analysis")
        
        if "ai_insights" not in offer_data or not offer_data["ai_insights"].get("markets"):
            st.warning("No market insights available for this offer.")
            return

        # Create tabs for different aspects of insights
        market_tab, metrics_tab, recommendations_tab = st.tabs([
            "Market Analysis", "Route Metrics", "Recommendations"
        ])

        with market_tab:
            markets = offer_data["ai_insights"]["markets"]
            
            # Create a radar chart for each market
            for market in markets:
                market_type = market["market_type"]
                region = market["region"]
                
                st.write(f"### {self.MARKET_TYPES.get(market_type, market_type)} ({region})")
                
                # Prepare data for radar chart
                indicators = market["indicators"]
                fig = go.Figure()
                
                fig.add_trace(go.Scatterpolar(
                    r=[indicators.get(ind, 0) * 100 for ind in self.INDICATOR_LABELS.keys()],
                    theta=list(self.INDICATOR_LABELS.values()),
                    fill='toself',
                    name=f'{region} Indicators'
                ))
                
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 100]
                        )
                    ),
                    showlegend=False,
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display metadata
                if "metadata" in market:
                    cols = st.columns(3)
                    with cols[0]:
                        st.metric("Confidence Score", f"{market['metadata'].get('confidence_score', 0)*100:.1f}%")
                    with cols[1]:
                        st.metric("Data Freshness", market['metadata'].get('data_freshness', 'N/A'))
                    with cols[2]:
                        st.metric("Market Volatility", market['metadata'].get('market_volatility', 'N/A'))

        with metrics_tab:
            if "route_metrics" in offer_data["ai_insights"]:
                metrics = offer_data["ai_insights"]["route_metrics"]
                cols = st.columns(3)
                
                with cols[0]:
                    st.metric(
                        "Efficiency Score",
                        f"{metrics.get('efficiency_score', 0)*100:.1f}%",
                        help="Route efficiency based on distance and time metrics"
                    )
                with cols[1]:
                    st.metric(
                        "Cost per KM",
                        f"€{metrics.get('cost_per_km', 0):.2f}",
                        help="Average cost per kilometer"
                    )
                with cols[2]:
                    st.metric(
                        "Time Efficiency",
                        f"{metrics.get('time_efficiency', 0):.2f}",
                        help="Time efficiency ratio (actual vs expected duration)"
                    )

        with recommendations_tab:
            if "recommendations" in offer_data["ai_insights"]:
                recommendations = offer_data["ai_insights"]["recommendations"]
                
                for rec in recommendations:
                    with st.expander(f"{rec['type'].title()} Recommendation - Priority: {rec['priority'].upper()}"):
                        st.write(rec['message'])
                        st.progress(rec.get('impact_score', 0))
                        st.caption(f"Impact Score: {rec.get('impact_score', 0)*100:.1f}%")

    def render(self) -> None:
        """Render the enhanced offer review page."""
        st.title("Offer Review")

        # Generate Offer button at the top
        if st.button("Generate Offer", type="primary"):
            try:
                # Call the API to generate a new offer
                response = requests.post(
                    f"{API_URL}/offers/generate",
                    headers=HEADERS
                )
                
                if response.status_code == 200:
                    generated_offer = response.json()
                    
                    # Display Offer Summary
                    st.write("## 📋 Offer Summary")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write("Base Cost")
                        st.write(f"€{generated_offer.get('base_cost', 0):.2f}")
                    with col2:
                        st.write("Margin")
                        st.write(f"{generated_offer.get('margin', 0)*100:.0f}%")
                    with col3:
                        st.write("Final Price")
                        st.write(f"€{generated_offer.get('final_price', 0):.2f}")
                    
                    # Display fun fact if available
                    if 'ai_insights' in generated_offer and 'fun_facts' in generated_offer['ai_insights']:
                        fun_facts = generated_offer['ai_insights']['fun_facts']
                        if fun_facts:
                            st.info(f"🚀 Fun Fact: {fun_facts[0]}")
                    
                    # Display feedback section
                    st.write("## 📝 Your Feedback")
                    st.write("Help us improve! Share your experience with our service.")
                    
                    feedback_rating = st.slider(
                        "Rate your experience",
                        min_value=1,
                        max_value=5,
                        value=3,
                        help="Rate the offer from 1 (poor) to 5 (excellent)"
                    )
                    
                    feedback_text = st.text_area(
                        "Additional comments (optional)",
                        placeholder="Share your thoughts about this offer..."
                    )
                    
                    if st.button("Submit Feedback", type="primary", key="submit_feedback"):
                        try:
                            feedback_data = {
                                "offer_id": generated_offer['id'],
                                "rating": feedback_rating,
                                "comments": feedback_text,
                                "timestamp": datetime.now().isoformat()
                            }
                            
                            feedback_response = requests.post(
                                f"{API_URL}/offers/{generated_offer['id']}/feedback",
                                headers=HEADERS,
                                json=feedback_data
                            )
                            
                            if feedback_response.status_code == 200:
                                st.success("Thank you for your feedback!")
                            else:
                                st.error("Failed to submit feedback. Please try again.")
                                
                        except Exception as e:
                            st.error(f"Error submitting feedback: {str(e)}")
                    
                    # Store the generated offer and display details
                    self.selected_offer = generated_offer
                    self.render_offer_details(generated_offer)
                else:
                    st.error("Failed to generate offer. Please try again.")
            except Exception as e:
                st.error(f"Error generating offer: {str(e)}")
        
        # Rest of the existing render code for viewing offers
        if not self.offers:
            return
            
        st.write("### Previous Offers")
        st.write(f"Showing {len(self.offers)} of {self.total_offers} offers")
        
        # Fetch offers based on filters
        self.fetch_offers()
        
        # Display offers table
        if self.df is not None:
            st.dataframe(
                self.df[[
                    'id', 'status', 'final_price', 'currency',
                    'created_at', 'client_name'
                ]],
                height=400
            )
        
        # Offer selection
        selected_offer_id = st.selectbox(
            "Select an offer to view details",
            options=[offer['id'] for offer in self.offers],
            format_func=lambda x: f"Offer {x[:8]}... - {next((o['client_name'] for o in self.offers if o['id'] == x), 'N/A')}"
        )
        
        if selected_offer_id:
            self.selected_offer = next(
                (offer for offer in self.offers if offer['id'] == selected_offer_id),
                None
            )
            
            if self.selected_offer:
                # Display Offer Summary first
                st.write("## 📋 Offer Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write("Base Cost")
                    st.write(f"€{self.selected_offer.get('base_cost', 0):.2f}")
                with col2:
                    st.write("Margin")
                    st.write(f"{self.selected_offer.get('margin', 0)*100:.0f}%")
                with col3:
                    st.write("Final Price")
                    st.write(f"€{self.selected_offer.get('final_price', 0):.2f}")
                
                # Display fun fact if available
                if 'ai_insights' in self.selected_offer and 'fun_facts' in self.selected_offer['ai_insights']:
                    fun_facts = self.selected_offer['ai_insights']['fun_facts']
                    if fun_facts:
                        st.info(f"🚀 Fun Fact: {fun_facts[0]}")
                
                # Display feedback section after offer summary
                st.write("## 📝 Your Feedback")
                st.write("Help us improve! Share your experience with our service.")
                
                feedback_rating = st.slider(
                    "Rate your experience",
                    min_value=1,
                    max_value=5,
                    value=3,
                    help="Rate the offer from 1 (poor) to 5 (excellent)"
                )
                
                feedback_text = st.text_area(
                    "Additional comments (optional)",
                    placeholder="Share your thoughts about this offer..."
                )
                
                if st.button("Submit Feedback", type="primary"):
                    try:
                        feedback_data = {
                            "offer_id": self.selected_offer['id'],
                            "rating": feedback_rating,
                            "comments": feedback_text,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        response = requests.post(
                            f"{API_URL}/offers/{self.selected_offer['id']}/feedback",
                            headers=HEADERS,
                            json=feedback_data
                        )
                        
                        if response.status_code == 200:
                            st.success("Thank you for your feedback!")
                        else:
                            st.error("Failed to submit feedback. Please try again.")
                            
                    except Exception as e:
                        st.error(f"Error submitting feedback: {str(e)}")
                
                # Display detailed tabs after feedback section
                self.render_offer_details(self.selected_offer)


def render_offer_review_page():
    """Helper function to render the offer review page."""
    page = OfferReviewPage()
    page.render()
