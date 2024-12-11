import pytest
from tests.api.base_test import BaseAPITest
from datetime import datetime, timedelta
from uuid import uuid4

class TestContractEndpoints(BaseAPITest):
    def test_create_contract(self, client, mock_route):
        """Test contract creation endpoint"""
        payload = {
            "route_id": str(mock_route.id),
            "client_id": str(uuid4()),
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "terms": {
                "payment_terms": "NET30",
                "currency": "EUR",
                "special_conditions": []
            }
        }

        response = self.client.post(f"{self.base_url}/contracts", json=payload)
        assert response.status_code == 201
        data = response.get_json()
        
        assert "id" in data
        assert "route_id" in data
        assert data["status"] == "draft"

    def test_get_contract(self, client):
        """Test getting contract details"""
        contract_id = str(uuid4())
        response = self.client.get(f"{self.base_url}/contracts/{contract_id}")
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["id"] == contract_id
        assert "terms" in data
        assert "status" in data

    def test_update_contract_status(self, client):
        """Test updating contract status"""
        contract_id = str(uuid4())
        payload = {
            "status": "active",
            "updated_by": str(uuid4())
        }

        response = self.client.patch(
            f"{self.base_url}/contracts/{contract_id}/status",
            json=payload
        )
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["status"] == "active"
        assert "updated_at" in data

    def test_invalid_contract_update(self, client):
        """Test invalid contract status update"""
        contract_id = str(uuid4())
        payload = {
            "status": "invalid_status",
            "updated_by": str(uuid4())
        }

        response = self.client.patch(
            f"{self.base_url}/contracts/{contract_id}/status",
            json=payload
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data 