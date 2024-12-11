import json
from uuid import uuid4

def test_create_offer(client, test_route):
    """Test /offer endpoint for creating an offer with fun fact."""
    data = {
        "route_id": test_route.id,
        "margin": 15.0
    }

    response = client.post('/offer',
                          data=json.dumps(data),
                          content_type='application/json')
    
    assert response.status_code == 201
    offer_data = json.loads(response.data)
    
    assert "id" in offer_data
    assert "route_id" in offer_data
    assert "total_price" in offer_data
    assert "margin" in offer_data
    assert "fun_fact" in offer_data
    assert offer_data["route_id"] == test_route.id
    assert offer_data["margin"] == 15.0
    assert isinstance(offer_data["fun_fact"], str)
    assert len(offer_data["fun_fact"]) > 0

def test_create_offer_invalid_input(client):
    """Test /offer endpoint with invalid input."""
    # Test missing route_id
    response = client.post('/offer',
                          data=json.dumps({"margin": 15.0}),
                          content_type='application/json')
    assert response.status_code == 400
    
    # Test missing margin
    response = client.post('/offer',
                          data=json.dumps({"route_id": str(uuid4())}),
                          content_type='application/json')
    assert response.status_code == 400

def test_review_offers(client, test_offer):
    """Test /data/review endpoint for reviewing past offers."""
    response = client.get('/data/review')
    
    assert response.status_code == 200
    review_data = json.loads(response.data)
    
    assert "offers" in review_data
    assert "total_count" in review_data
    assert isinstance(review_data["offers"], list)
    assert review_data["total_count"] > 0
    
    offer = review_data["offers"][0]
    assert "id" in offer
    assert "route_id" in offer
    assert "total_price" in offer
    assert "margin" in offer
    assert "fun_fact" in offer
    assert isinstance(offer["fun_fact"], str) 