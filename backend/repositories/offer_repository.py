from sqlalchemy import and_
from datetime import datetime
from typing import List, Tuple, Optional
from backend.models.offer import Offer
import structlog

class OfferRepository:
    def __init__(self, db_session):
        self.db_session = db_session
        self.logger = structlog.get_logger(__name__).bind(repository="OfferRepository")

    def list_offers(
        self,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        currency: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[List[Offer], int]:
        """
        List offers with pagination and filtering
        
        Args:
            min_price (float, optional): Minimum price filter
            max_price (float, optional): Maximum price filter
            start_date (str, optional): Start date filter (YYYY-MM-DD)
            end_date (str, optional): End date filter (YYYY-MM-DD)
            currency (str, optional): Currency filter
            status (str, optional): Status filter
            limit (int): Maximum number of items to return (default: 10)
            offset (int): Number of items to skip (default: 0)
            
        Returns:
            tuple: (list of Offer objects, total count)
        """
        try:
            query = self.db_session.query(Offer)
            
            # Track applied filters for logging
            applied_filters = []
            
            # Apply filters
            if min_price is not None:
                query = query.filter(Offer.final_price >= float(min_price))
                applied_filters.append('min_price')
            if max_price is not None:
                query = query.filter(Offer.final_price <= float(max_price))
                applied_filters.append('max_price')
            if start_date:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(Offer.created_at >= start)
                applied_filters.append('start_date')
            if end_date:
                end = datetime.strptime(end_date, '%Y-%m-%d')
                query = query.filter(Offer.created_at <= end)
                applied_filters.append('end_date')
            if currency:
                query = query.filter(Offer.currency == currency)
                applied_filters.append('currency')
            if status:
                query = query.filter(Offer.status == status)
                applied_filters.append('status')

            self.logger.info("filters_applied", filters=applied_filters)

            # Get total count before pagination
            total = query.count()
            self.logger.info("total_matching_offers", count=total)
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            # Execute query and ensure we return a list
            offers = list(query.all())
            
            has_more = total > (offset + len(offers))
            self.logger.info(
                "offers_retrieved",
                count=len(offers),
                page_info={
                    'limit': limit,
                    'offset': offset,
                    'has_more': has_more
                },
                total_matches=total
            )
            
            return offers, total

        except Exception as e:
            self.logger.error("list_offers_failed", error=str(e))
            # Return empty list and zero count on error
            return [], 0

    def get_offer_by_id(self, offer_id):
        """
        Retrieve a specific offer by ID
        
        Args:
            offer_id (UUID): ID of the offer to retrieve
            
        Returns:
            Offer: The offer object if found, None otherwise
        """
        return self.db_session.query(Offer).filter(Offer.id == offer_id).first()

    def create_offer(self, offer):
        """
        Create a new offer
        
        Args:
            offer (Offer): Offer object to create
            
        Returns:
            Offer: Created offer object
        """
        self.db_session.add(offer)
        self.db_session.commit()
        return offer

    def update_offer(self, offer):
        """
        Update an existing offer
        
        Args:
            offer (Offer): Offer object with updated values
            
        Returns:
            Offer: Updated offer object
        """
        self.db_session.merge(offer)
        self.db_session.commit()
        return offer

    def delete_offer(self, offer_id):
        """
        Delete an offer
        
        Args:
            offer_id (UUID): ID of the offer to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        offer = self.get_offer_by_id(offer_id)
        if offer:
            self.db_session.delete(offer)
            self.db_session.commit()
            return True
        return False