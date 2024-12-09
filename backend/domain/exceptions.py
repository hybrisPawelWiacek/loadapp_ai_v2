"""
Domain-specific exceptions for the LoadApp application.

This module defines the base exception classes used throughout the domain layer
to represent different categories of errors that can occur during business operations.
"""

class ValidationError(Exception):
    """
    Raised when input data fails validation rules.
    
    This exception is used when:
    - Required fields are missing
    - Field values are in incorrect format
    - Field values are outside acceptable ranges
    """
    def __init__(self, field: str = None, message: str = None):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}" if field else message)


class BusinessRuleError(Exception):
    """
    Raised when an operation would violate business rules.
    
    This exception is used when:
    - Business constraints would be violated
    - Operation timing is invalid
    - State transitions are not allowed
    """
    def __init__(self, rule: str = None, message: str = None):
        self.rule = rule
        self.message = message
        super().__init__(f"{rule}: {message}" if rule else message)


class ResourceNotFoundError(Exception):
    """
    Raised when a requested resource does not exist.
    
    This exception is used when:
    - Referenced entities don't exist in the system
    - Attempting to access deleted resources
    - Looking up non-existent identifiers
    """
    def __init__(self, resource_type: str = None, resource_id: str = None, message: str = None):
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.message = message
        super().__init__(
            f"{resource_type} with id {resource_id} not found" if resource_type and resource_id
            else message
        )


class RouteValidationException(ValidationError):
    """
    Raised when route validation fails.
    
    This exception is used when:
    - Cost settings validation fails
    - Timeline validation fails
    - Required settings are missing
    """
    def __init__(self, errors: list = None, message: str = None):
        self.errors = errors or []
        super().__init__(message=message or f"Route validation failed with {len(self.errors)} errors")
