import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from decimal import Decimal
from typing import Dict, Any

from backend.domain.entities.offer import Offer, OfferStatus, GeographicRestriction, BusinessRuleResult, OfferMetrics
from backend.infrastructure.database.repositories.offer_repository import OfferRepository, OfferWithCosts
from backend.infrastructure.database.models import OfferModel, OfferVersionModel, CostSetting

@pytest.fixture
def offer_repository(db_session):
    """Create an offer repository instance."""
    return OfferRepository(db_session)

@pytest.fixture
def sample_offer_data() -> Dict[str, Any]:
    """Create sample offer data."""
    return {
        "id": uuid4(),
        "route_id": uuid4(),
        "total_cost": Decimal("1000.00"),
        "margin": Decimal("0.15"),
        "final_price": Decimal("1150.00"),
        "currency": "EUR",
        "status": OfferStatus.DRAFT,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "cost_breakdown": {
            "base": Decimal("500.00"),
            "variable": Decimal("400.00"),
            "cargo": Decimal("100.00")
        },
        "applied_settings": [
            {"type": "fuel", "value": 1.5},
            {"type": "driver", "value": 200}
        ],
        "ai_insights": ["Consider night delivery for lower costs"],
        "version": 1,
        "metadata": {"client_id": str(uuid4())},
        "geographic_restrictions": GeographicRestriction(
            allowed_countries=["DE", "FR"],
            allowed_regions=["EU"],
            restricted_zones=["ALPS"]
        ),
        "business_rules_validation": [
            BusinessRuleResult(rule_id="R1", passed=True, message="All checks passed"),
            BusinessRuleResult(rule_id="R2", passed=True, message="Route valid")
        ],
        "metrics": OfferMetrics(
            processing_time_ms=150,
            ai_processing_time_ms=100,
            route_calculation_time_ms=50
        )
    }

@pytest.mark.unit
class TestOfferRepository:
    """Test suite for OfferRepository."""

    def test_create_offer(self, offer_repository, sample_offer_data):
        """Test creating a new offer."""
        # Create offer entity
        offer = Offer(**sample_offer_data)
        
        # Save offer
        created_offer = offer_repository.create_offer(offer)
        
        # Verify created offer
        assert created_offer.id == offer.id
        assert created_offer.route_id == offer.route_id
        assert created_offer.total_cost == offer.total_cost
        assert created_offer.margin == offer.margin
        assert created_offer.final_price == offer.final_price
        assert created_offer.status == offer.status
        assert created_offer.cost_breakdown == offer.cost_breakdown
        assert created_offer.geographic_restrictions.allowed_countries == ["DE", "FR"]
        assert len(created_offer.business_rules_validation) == 2
        assert created_offer.metrics.processing_time_ms == 150

    def test_list_offers_with_filters(self, offer_repository, sample_offer_data):
        """Test listing offers with various filters."""
        # Create multiple offers with different attributes
        offer1 = Offer(**sample_offer_data)
        
        offer2_data = sample_offer_data.copy()
        offer2_data.update({
            "id": uuid4(),
            "final_price": Decimal("2000.00"),
            "status": OfferStatus.ACCEPTED,
            "created_at": datetime.utcnow() - timedelta(days=5)
        })
        offer2 = Offer(**offer2_data)
        
        offer3_data = sample_offer_data.copy()
        offer3_data.update({
            "id": uuid4(),
            "final_price": Decimal("3000.00"),
            "status": OfferStatus.PENDING,
            "created_at": datetime.utcnow() - timedelta(days=10)
        })
        offer3 = Offer(**offer3_data)
        
        # Save offers
        offer_repository.create_offer(offer1)
        offer_repository.create_offer(offer2)
        offer_repository.create_offer(offer3)
        
        # Test different filter combinations
        filters = {
            "min_price": 1500,
            "max_price": 2500,
            "status": OfferStatus.ACCEPTED,
            "start_date": datetime.utcnow() - timedelta(days=7),
            "end_date": datetime.utcnow()
        }
        
        offers, total_count = offer_repository.list_offers_with_filters(filters)
        
        assert len(offers) == 1
        assert total_count == 1
        assert offers[0].final_price == Decimal("2000.00")
        assert offers[0].status == OfferStatus.ACCEPTED

    def test_delete_offer(self, offer_repository, sample_offer_data):
        """Test offer deletion (soft delete)."""
        # Create and save offer
        offer = Offer(**sample_offer_data)
        created_offer = offer_repository.create_offer(offer)
        
        # Delete offer
        success = offer_repository.delete_offer(created_offer.id)
        assert success is True
        
        # Verify offer is soft deleted
        filters = {"status": OfferStatus.EXPIRED}
        offers, _ = offer_repository.list_offers_with_filters(filters)
        assert len(offers) == 1
        assert offers[0].id == created_offer.id

    def test_get_offer_with_costs(self, offer_repository, sample_offer_data):
        """Test retrieving offer with detailed cost information."""
        # Create and save offer
        offer = Offer(**sample_offer_data)
        created_offer = offer_repository.create_offer(offer)
        
        # Get offer with costs
        offer_with_costs = offer_repository.get_offer_with_costs(created_offer.id)
        
        assert isinstance(offer_with_costs, OfferWithCosts)
        assert offer_with_costs.offer.id == created_offer.id
        assert "base" in offer_with_costs.cost_breakdown
        assert len(offer_with_costs.applied_settings) == 2
        assert offer_with_costs.applied_settings[0]["type"] == "fuel"

    def test_entity_model_conversion(self, offer_repository, sample_offer_data):
        """Test entity to model and model to entity conversion."""
        # Create offer entity
        offer = Offer(**sample_offer_data)
        
        # Convert to model
        model = offer_repository._to_model(offer)
        
        assert isinstance(model, OfferModel)
        assert str(model.id) == str(offer.id)
        assert model.total_cost == offer.total_cost
        assert model.margin == offer.margin
        assert model.final_price == offer.final_price
        assert model.status == offer.status
        assert model.cost_breakdown == offer.cost_breakdown
        
        # Convert back to entity
        entity = offer_repository._to_entity(model)
        
        assert isinstance(entity, Offer)
        assert entity.id == offer.id
        assert entity.total_cost == offer.total_cost
        assert entity.margin == offer.margin
        assert entity.final_price == offer.final_price
        assert entity.status == offer.status
        assert entity.cost_breakdown == offer.cost_breakdown

    def test_error_handling(self, offer_repository, sample_offer_data):
        """Test error handling in repository operations."""
        # Test invalid offer ID
        with pytest.raises(Exception):
            offer_repository.get_offer_with_costs(uuid4())
        
        # Test invalid filter values
        with pytest.raises(Exception):
            filters = {"min_price": "invalid"}
            offer_repository.list_offers_with_filters(filters)
        
        # Test deleting non-existent offer
        success = offer_repository.delete_offer(uuid4())
        assert success is False

    def test_version_tracking(self, offer_repository, sample_offer_data):
        """Test offer version tracking."""
        # Create initial offer
        offer = Offer(**sample_offer_data)
        created_offer = offer_repository.create_offer(offer)
        
        # Verify initial version
        assert created_offer.version == 1
        
        # Update offer
        created_offer.margin = Decimal("0.20")
        created_offer.version += 1
        updated_offer = offer_repository.create_offer(created_offer)
        
        # Verify version increment
        assert updated_offer.version == 2
        
        # Check version history
        versions = offer_repository.session.query(OfferVersionModel).filter(
            OfferVersionModel.offer_id == created_offer.id
        ).all()
        
        assert len(versions) == 2
        assert versions[0].version == 1
        assert versions[1].version == 2 