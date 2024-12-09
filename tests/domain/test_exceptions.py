"""Tests for domain exceptions."""

import pytest
from backend.domain.exceptions import ValidationError, BusinessRuleError, ResourceNotFoundError


class TestValidationError:
    def test_validation_error_with_field_and_message(self):
        """Test ValidationError with both field and message."""
        error = ValidationError(field="distance_km", message="Distance cannot be negative")
        assert str(error) == "distance_km: Distance cannot be negative"
        assert error.field == "distance_km"
        assert error.message == "Distance cannot be negative"

    def test_validation_error_with_message_only(self):
        """Test ValidationError with message only."""
        error = ValidationError(message="Invalid input")
        assert str(error) == "Invalid input"
        assert error.field is None
        assert error.message == "Invalid input"

    def test_validation_error_empty(self):
        """Test ValidationError with no arguments."""
        error = ValidationError()
        assert str(error) == "None: None"
        assert error.field is None
        assert error.message is None


class TestBusinessRuleError:
    def test_business_rule_error_with_rule_and_message(self):
        """Test BusinessRuleError with both rule and message."""
        error = BusinessRuleError(rule="route_timing", message="Delivery time must be after pickup time")
        assert str(error) == "route_timing: Delivery time must be after pickup time"
        assert error.rule == "route_timing"
        assert error.message == "Delivery time must be after pickup time"

    def test_business_rule_error_with_message_only(self):
        """Test BusinessRuleError with message only."""
        error = BusinessRuleError(message="Business rule violated")
        assert str(error) == "Business rule violated"
        assert error.rule is None
        assert error.message == "Business rule violated"

    def test_business_rule_error_empty(self):
        """Test BusinessRuleError with no arguments."""
        error = BusinessRuleError()
        assert str(error) == "None: None"
        assert error.rule is None
        assert error.message is None


class TestResourceNotFoundError:
    def test_resource_not_found_error_with_all_args(self):
        """Test ResourceNotFoundError with all arguments."""
        error = ResourceNotFoundError(resource_type="Offer", resource_id="123", message="Custom message")
        assert str(error) == "Offer with id 123 not found"
        assert error.resource_type == "Offer"
        assert error.resource_id == "123"
        assert error.message == "Custom message"

    def test_resource_not_found_error_with_custom_message(self):
        """Test ResourceNotFoundError with custom message only."""
        error = ResourceNotFoundError(message="Resource not found")
        assert str(error) == "Resource not found"
        assert error.resource_type is None
        assert error.resource_id is None
        assert error.message == "Resource not found"

    def test_resource_not_found_error_empty(self):
        """Test ResourceNotFoundError with no arguments."""
        error = ResourceNotFoundError()
        assert str(error) == "None"
        assert error.resource_type is None
        assert error.resource_id is None
        assert error.message is None


def test_exceptions_inheritance():
    """Test that all exceptions inherit from Exception."""
    assert issubclass(ValidationError, Exception)
    assert issubclass(BusinessRuleError, Exception)
    assert issubclass(ResourceNotFoundError, Exception)


def test_exceptions_can_be_caught():
    """Test that exceptions can be caught and handled properly."""
    
    def raise_validation_error():
        raise ValidationError(field="test", message="test error")
        
    def raise_business_rule_error():
        raise BusinessRuleError(rule="test", message="test error")
        
    def raise_resource_not_found_error():
        raise ResourceNotFoundError(resource_type="Test", resource_id="123")

    # Test ValidationError
    with pytest.raises(ValidationError) as exc_info:
        raise_validation_error()
    assert exc_info.value.field == "test"
    assert exc_info.value.message == "test error"

    # Test BusinessRuleError
    with pytest.raises(BusinessRuleError) as exc_info:
        raise_business_rule_error()
    assert exc_info.value.rule == "test"
    assert exc_info.value.message == "test error"

    # Test ResourceNotFoundError
    with pytest.raises(ResourceNotFoundError) as exc_info:
        raise_resource_not_found_error()
    assert exc_info.value.resource_type == "Test"
    assert exc_info.value.resource_id == "123"
