from flask import request, jsonify
from flask_restful import Resource
from uuid import UUID
import structlog

from backend.domain.services import OfferService
from backend.domain.entities import Offer
from backend.api.dtos import OfferResponse

class OfferEndpoint(Resource):
    """Endpoint for managing offers."""

    def __init__(self, offer_service: OfferService):
        """Initialize with required services."""
        self.offer_service = offer_service
        self.logger = structlog.get_logger(__name__)

    def post(self):
        """Create a new offer."""
        try:
            data = request.get_json()
            if not data:
                return {"error": "No data provided"}, 400

            # Validate required fields
            if "route_id" not in data:
                return {"error": "route_id is required"}, 400
            if "margin" not in data:
                return {"error": "margin is required"}, 400

            # Convert route_id to UUID
            try:
                route_id = UUID(data["route_id"])
            except ValueError:
                return {"error": "Invalid route_id format"}, 400

            # Create offer
            offer = self.offer_service.create_offer(
                route_id=route_id,
                margin=float(data["margin"]),
                client_name=data.get("client_name"),
                client_contact=data.get("client_contact"),
                geographic_restrictions=data.get("geographic_restrictions")
            )

            # Convert to response DTO
            response = OfferResponse(
                id=str(offer.id),
                route_id=str(offer.route_id),
                total_cost=float(offer.cost_breakdown.total_cost),
                margin=float(offer.margin_percentage),
                final_price=float(offer.final_price),
                currency=offer.currency.value,
                status=offer.status.value,
                created_at=offer.created_at.isoformat(),
                updated_at=offer.updated_at.isoformat(),
                cost_breakdown=offer.cost_breakdown.to_dict(),
                applied_settings=offer.applied_settings,
                ai_insights=offer.ai_insights,
                geographic_restrictions=offer.geographic_restrictions.to_dict() if offer.geographic_restrictions else None,
                metrics=offer.metrics.to_dict() if hasattr(offer, 'metrics') and offer.metrics else None
            )

            return response.to_dict(), 201

        except Exception as e:
            self.logger.error("create_offer_failed", error=str(e))
            return {"error": str(e)}, 500

    def get(self, offer_id: str = None):
        """Get an offer by ID or list offers with filters."""
        try:
            if offer_id:
                # Get single offer
                try:
                    offer_uuid = UUID(offer_id)
                except ValueError:
                    return {"error": "Invalid offer_id format"}, 400

                offer = self.offer_service.get_offer(offer_uuid)
                if not offer:
                    return {"error": "Offer not found"}, 404

                response = OfferResponse(
                    id=str(offer.id),
                    route_id=str(offer.route_id),
                    total_cost=float(offer.cost_breakdown.total_cost),
                    margin=float(offer.margin_percentage),
                    final_price=float(offer.final_price),
                    currency=offer.currency.value,
                    status=offer.status.value,
                    created_at=offer.created_at.isoformat(),
                    updated_at=offer.updated_at.isoformat(),
                    cost_breakdown=offer.cost_breakdown.to_dict(),
                    applied_settings=offer.applied_settings,
                    ai_insights=offer.ai_insights,
                    geographic_restrictions=offer.geographic_restrictions.to_dict() if offer.geographic_restrictions else None,
                    metrics=offer.metrics.to_dict() if hasattr(offer, 'metrics') and offer.metrics else None
                )

                return response.to_dict(), 200

            else:
                # List offers with filters
                filters = request.args.to_dict()
                page = int(filters.pop("page", 1))
                page_size = int(filters.pop("page_size", 10))

                try:
                    offers, total = self.offer_service.list_offers(
                        filters=filters,
                        page=page,
                        page_size=page_size
                    )
                except Exception as e:
                    self.logger.error("list_offers_failed", error=str(e))
                    offers, total = [], 0

                response = {
                    "offers": [
                        OfferResponse(
                            id=str(offer.id),
                            route_id=str(offer.route_id),
                            total_cost=float(offer.cost_breakdown.total_cost),
                            margin=float(offer.margin_percentage),
                            final_price=float(offer.final_price),
                            currency=offer.currency.value,
                            status=offer.status.value,
                            created_at=offer.created_at.isoformat(),
                            updated_at=offer.updated_at.isoformat(),
                            cost_breakdown=offer.cost_breakdown.to_dict(),
                            applied_settings=offer.applied_settings,
                            ai_insights=offer.ai_insights,
                            geographic_restrictions=offer.geographic_restrictions.to_dict() if offer.geographic_restrictions else None,
                            metrics=offer.metrics.to_dict() if hasattr(offer, 'metrics') and offer.metrics else None
                        ).to_dict()
                        for offer in offers
                    ] if offers else [],
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }

                return response, 200

        except Exception as e:
            self.logger.error("get_offer_failed", error=str(e))
            return {"error": str(e)}, 500

    def put(self, offer_id: str):
        """Update an offer."""
        try:
            # Validate offer_id
            try:
                offer_uuid = UUID(offer_id)
            except ValueError:
                return {"error": "Invalid offer_id format"}, 400

            data = request.get_json()
            if not data:
                return {"error": "No data provided"}, 400

            # Update offer
            offer = self.offer_service.update_offer(
                offer_id=offer_uuid,
                updates=data,
                user_id=request.headers.get("X-User-ID"),
                reason=data.get("update_reason", "Manual update")
            )

            response = OfferResponse(
                id=str(offer.id),
                route_id=str(offer.route_id),
                total_cost=float(offer.cost_breakdown.total_cost),
                margin=float(offer.margin_percentage),
                final_price=float(offer.final_price),
                currency=offer.currency.value,
                status=offer.status.value,
                created_at=offer.created_at.isoformat(),
                updated_at=offer.updated_at.isoformat(),
                cost_breakdown=offer.cost_breakdown.to_dict(),
                applied_settings=offer.applied_settings,
                ai_insights=offer.ai_insights,
                geographic_restrictions=offer.geographic_restrictions.to_dict() if offer.geographic_restrictions else None,
                metrics=offer.metrics.to_dict() if hasattr(offer, 'metrics') and offer.metrics else None
            )

            return response.to_dict(), 200

        except Exception as e:
            self.logger.error("update_offer_failed", error=str(e))
            return {"error": str(e)}, 500

    def delete(self, offer_id: str):
        """Delete an offer."""
        try:
            # Validate offer_id
            try:
                offer_uuid = UUID(offer_id)
            except ValueError:
                return {"error": "Invalid offer_id format"}, 400

            # Delete offer
            success = self.offer_service.delete_offer(
                offer_id=offer_uuid,
                user_id=request.headers.get("X-User-ID"),
                reason=request.args.get("reason", "Manual deletion")
            )

            if success:
                return {"message": "Offer deleted successfully"}, 204
            else:
                return {"error": "Failed to delete offer"}, 500

        except Exception as e:
            self.logger.error("delete_offer_failed", error=str(e))
            return {"error": str(e)}, 500

    def get_offers(self):
        """Get all offers"""
        try:
            offers = self.offer_service.get_offers()
            return jsonify({
                'status': 'success',
                'data': [offer.to_dict() for offer in offers]
            })
        except Exception as e:
            return {'error': str(e)}, 500
