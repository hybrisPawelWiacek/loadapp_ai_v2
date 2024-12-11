import pytest
from tests.api.base_test import BaseAPITest
from datetime import datetime, timedelta

class TestRouteEndpoints(BaseAPITest):
    def test_create_route(self, client, mock_location):
        """Test route creation endpoint"""
        payload = {
            "origin": {
                "latitude": mock_location.latitude,
                "longitude": mock_location.longitude,
                "address": mock_location.address
            },
            "destination": {
                "latitude": 48.8566,
                "longitude": 2.3522,
                "address": "Paris, France"
            },
            "pickup_time": datetime.now().isoformat(),
            "delivery_time": (datetime.now() + timedelta(days=1)).isoformat()
        }

        response = self.client.post(f"{self.base_url}/routes", json=payload)
        assert response.status_code == 201
        data = response.get_json()
        
        assert "id" in data
        assert "origin" in data
        assert "destination" in data
        assert data["is_feasible"] is True

    def test_get_route(self, client, mock_route):
        """Test getting route details"""
        response = self.client.get(f"{self.base_url}/routes/{mock_route.id}")
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["id"] == str(mock_route.id)
        assert data["origin"]["address"] == mock_route.origin.address
        assert data["destination"]["address"] == mock_route.destination.address

    def test_invalid_route(self, client):
        """Test creating invalid route"""
        payload = {
            "origin": {},  # Invalid origin
            "destination": {},  # Invalid destination
        }

        response = self.client.post(f"{self.base_url}/routes", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
