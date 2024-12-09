from flask import request, jsonify
from flask_restful import Resource

from ...domain.services import OfferService
from ...infrastructure.database import Repository

class OfferEndpoint(Resource):
    def __init__(self):
        self.offer_service = OfferService()
        self.repository = Repository()

    def post(self):
        """Generate a new offer."""
        try:
            data = request.get_json()
            offer = self.offer_service.generate_offer(
                route_id=data["route_id"],
                margin=data.get("margin", 10.0)
            )
            return {
                "id": str(offer.id),
                "route_id": str(offer.route_id),
                "total_price": offer.total_price,
                "margin": offer.margin,
                "cost_breakdown": offer.cost_breakdown,
                "status": offer.status,
                "created_at": offer.created_at.isoformat(),
                "updated_at": offer.updated_at.isoformat() if offer.updated_at else None,
                "client_name": offer.client_name,
                "client_contact": offer.client_contact,
                "ai_insights": offer.ai_insights
            }, 201
        except KeyError as e:
            return {"error": f"Missing required field: {str(e)}"}, 400
        except Exception as e:
            return {"error": str(e)}, 500

    def get(self, offer_id=None):
        """Get offer details."""
        try:
            if offer_id:
                offer = self.repository.get_offer(offer_id)
                if not offer:
                    return {"error": "Offer not found"}, 404
                return offer.to_dict(), 200
            else:
                offers = self.repository.get_offers()
                return jsonify([offer.to_dict() for offer in offers])
        except Exception as e:
            return {"error": str(e)}, 500

    def put(self, offer_id):
        """Update offer status."""
        try:
            data = request.get_json()
            offer = self.repository.update_offer(
                offer_id=offer_id,
                status=data["status"]
            )
            return offer.to_dict(), 200
        except KeyError as e:
            return {"error": f"Missing required field: {str(e)}"}, 400
        except Exception as e:
            return {"error": str(e)}, 500
