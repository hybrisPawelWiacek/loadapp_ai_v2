import pytest
import streamlit as st
from datetime import datetime, timedelta, UTC
from uuid import uuid4
from importlib import import_module

# Import using string literal to handle emoji in filename
offer_review = import_module("frontend.pages.1_📊_Offer_Review")

class TestOfferReviewPage:
    @pytest.fixture(autouse=True)
    def setup(self, mock_api_client):
        """Setup test environment with mocked API client"""
        # Reset Streamlit session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Initialize test data
        self.test_offer = {
            "id": str(uuid4()),
            "route_id": str(uuid4()),
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "base_price": 1000.0,
            "margin_percentage": 15.0,
            "final_price": 1150.0,
            "currency": "EUR",
            "cost_breakdown": {
                "base_costs": {"insurance": 200.0, "overhead": 300.0},
                "variable_costs": {"fuel": 400.0, "driver": 100.0},
                "cargo_costs": {}
            },
            "route": {
                "origin": {"address": "Berlin, Germany"},
                "destination": {"address": "Paris, France"},
                "distance_km": 1000.0,
                "duration_hours": 12.0
            }
        }

    def test_initialize_filters(self):
        """Test filter initialization"""
        filters = offer_review.initialize_filters()
        assert filters is not None
        assert filters.min_price >= 0
        assert filters.max_price > filters.min_price
        assert filters.status in ["all", "pending", "accepted", "rejected"]
        assert filters.currency in ["EUR", "USD", "GBP"]

    def test_fetch_offers(self, monkeypatch):
        """Test fetching offers"""
        # Mock API response
        def mock_get(*args, **kwargs):
            return type('Response', (), {
                'status_code': 200,
                'json': lambda: {"offers": [self.test_offer], "total": 1}
            })()
        
        monkeypatch.setattr("requests.get", mock_get)
        
        # Test fetching offers
        filters = offer_review.initialize_filters()
        offers, total = offer_review.fetch_offers(filters)
        
        assert len(offers) == 1
        assert total == 1
        assert offers[0]["id"] == self.test_offer["id"]

    def test_display_analytics(self):
        """Test analytics display"""
        import pandas as pd
        df = pd.DataFrame([{
            'final_price': 1150.0,
            'margin_percentage': 15.0,
            'status': 'accepted',
            'created_at': datetime.now()
        }])
        
        offer_review.display_analytics(df)
        
        # Verify metrics in session state
        assert 'Average Price' in st.session_state
        assert 'Average Margin' in st.session_state
        assert 'Total Offers' in st.session_state
        assert 'Success Rate' in st.session_state

    def test_display_offer_details(self, monkeypatch):
        """Test offer details display"""
        # Mock route API response
        def mock_get(*args, **kwargs):
            return type('Response', (), {
                'status_code': 200,
                'json': lambda: {
                    "origin": {"address": "Berlin, Germany"},
                    "destination": {"address": "Paris, France"},
                    "total_duration_hours": 12.0,
                    "timeline": []
                }
            })()
        
        monkeypatch.setattr("requests.get", mock_get)
        
        # Test displaying offer details
        offer_review.display_offer_details(self.test_offer)
        
        # Verify tabs are created
        assert 'Overview' in st.session_state
        assert 'Route Details' in st.session_state
        assert 'Cost Breakdown' in st.session_state
        assert 'Market Analysis' in st.session_state