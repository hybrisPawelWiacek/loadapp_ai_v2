from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from uuid import UUID
from datetime import datetime

from ..entities.cost_setting import CostSetting

@dataclass
class ValidationError:
    """Result of a cost setting validation."""
    setting_id: Optional[UUID]  # ID of the setting that failed validation
    code: str  # Error code for categorization
    message: str  # Human-readable error message
    severity: str = "error"  # error, warning
    context: Optional[Dict] = None  # Additional context about the error

class CostSettingValidator:
    """Validator for cost settings."""

    VALID_CATEGORIES = {"base", "variable", "cargo-specific"}
    VALID_TYPES = {
        "fuel", "maintenance", "time", "weight", 
        "volume", "handling", "insurance", "overhead"
    }
    VALID_CURRENCIES = {"EUR", "USD", "GBP"}
    
    # Business rule constants
    MAX_MULTIPLIER = 10.0
    MIN_BASE_VALUE = 0.01
    MAX_BASE_VALUE = 1000000.0  # 1M
    MAX_NAME_LENGTH = 100
    
    # Type-specific validation rules
    TYPE_RULES = {
        "fuel": {
            "min_value": 0.1,  # Minimum €0.10 per unit
            "max_value": 5.0,  # Maximum €5.00 per unit
            "required_category": "variable"
        },
        "maintenance": {
            "min_value": 0.05,
            "max_value": 10.0,
            "required_category": "variable"
        },
        "time": {
            "min_value": 1.0,  # Minimum €1.00 per hour
            "max_value": 200.0,  # Maximum €200.00 per hour
            "required_category": "variable"
        },
        "weight": {
            "min_value": 0.01,
            "max_value": 1.0,
            "required_category": "cargo-specific"
        }
    }
    
    # Combination rules
    REQUIRED_TYPES = {"fuel", "maintenance", "time"}  # Must have these types
    INCOMPATIBLE_TYPES = {
        "weight": {"volume"},  # Can't have both weight and volume based
        "insurance": {"overhead"}  # Can't have both insurance and overhead
    }

    def validate_setting(self, setting: CostSetting) -> List[ValidationError]:
        """
        Validate a single cost setting against basic rules.
        
        Args:
            setting: CostSetting to validate
            
        Returns:
            List of ValidationError objects
        """
        errors = []
        
        # Basic field validation
        if not setting.name:
            errors.append(ValidationError(
                setting_id=setting.id,
                code="MISSING_NAME",
                message="Name is required"
            ))
        elif len(setting.name) > self.MAX_NAME_LENGTH:
            errors.append(ValidationError(
                setting_id=setting.id,
                code="NAME_TOO_LONG",
                message=f"Name must be less than {self.MAX_NAME_LENGTH} characters"
            ))
            
        if not setting.type:
            errors.append(ValidationError(
                setting_id=setting.id,
                code="MISSING_TYPE",
                message="Type is required"
            ))
        elif setting.type not in self.VALID_TYPES:
            errors.append(ValidationError(
                setting_id=setting.id,
                code="INVALID_TYPE",
                message=f"Invalid type. Must be one of: {', '.join(self.VALID_TYPES)}"
            ))
            
        if not setting.category:
            errors.append(ValidationError(
                setting_id=setting.id,
                code="MISSING_CATEGORY",
                message="Category is required"
            ))
        elif setting.category not in self.VALID_CATEGORIES:
            errors.append(ValidationError(
                setting_id=setting.id,
                code="INVALID_CATEGORY",
                message=f"Invalid category. Must be one of: {', '.join(self.VALID_CATEGORIES)}"
            ))
            
        if setting.currency not in self.VALID_CURRENCIES:
            errors.append(ValidationError(
                setting_id=setting.id,
                code="INVALID_CURRENCY",
                message=f"Invalid currency. Must be one of: {', '.join(self.VALID_CURRENCIES)}"
            ))
            
        # Add business rule validation
        errors.extend(self.validate_business_rules(setting))
            
        return errors

    def validate_business_rules(self, setting: CostSetting) -> List[ValidationError]:
        """
        Validate business rules for a single setting.
        
        Args:
            setting: CostSetting to validate
            
        Returns:
            List of ValidationError objects
        """
        errors = []
        
        # Validate base value range
        if setting.base_value < self.MIN_BASE_VALUE:
            errors.append(ValidationError(
                setting_id=setting.id,
                code="BASE_VALUE_TOO_LOW",
                message=f"Base value must be at least {self.MIN_BASE_VALUE}",
                context={"min_value": self.MIN_BASE_VALUE}
            ))
        elif setting.base_value > self.MAX_BASE_VALUE:
            errors.append(ValidationError(
                setting_id=setting.id,
                code="BASE_VALUE_TOO_HIGH",
                message=f"Base value cannot exceed {self.MAX_BASE_VALUE}",
                context={"max_value": self.MAX_BASE_VALUE}
            ))
            
        # Validate multiplier range
        if setting.multiplier <= 0:
            errors.append(ValidationError(
                setting_id=setting.id,
                code="INVALID_MULTIPLIER",
                message="Multiplier must be greater than 0"
            ))
        elif setting.multiplier > self.MAX_MULTIPLIER:
            errors.append(ValidationError(
                setting_id=setting.id,
                code="MULTIPLIER_TOO_HIGH",
                message=f"Multiplier cannot exceed {self.MAX_MULTIPLIER}",
                severity="warning"
            ))
            
        # Type-specific validation
        if setting.type in self.TYPE_RULES:
            rules = self.TYPE_RULES[setting.type]
            
            if setting.base_value < rules["min_value"]:
                errors.append(ValidationError(
                    setting_id=setting.id,
                    code="TYPE_SPECIFIC_VALUE_TOO_LOW",
                    message=f"{setting.type} base value must be at least {rules['min_value']}",
                    context={"type": setting.type, "min_value": rules["min_value"]}
                ))
                
            if setting.base_value > rules["max_value"]:
                errors.append(ValidationError(
                    setting_id=setting.id,
                    code="TYPE_SPECIFIC_VALUE_TOO_HIGH",
                    message=f"{setting.type} base value cannot exceed {rules['max_value']}",
                    context={"type": setting.type, "max_value": rules["max_value"]}
                ))
                
            if setting.category != rules["required_category"]:
                errors.append(ValidationError(
                    setting_id=setting.id,
                    code="INVALID_TYPE_CATEGORY",
                    message=f"{setting.type} must be in category {rules['required_category']}",
                    context={"type": setting.type, "required_category": rules["required_category"]}
                ))
                
        return errors

    def validate_combinations(self, settings: List[CostSetting]) -> List[ValidationError]:
        """
        Validate combinations of settings.
        
        Args:
            settings: List of CostSettings to validate
            
        Returns:
            List of ValidationError objects
        """
        errors = []
        seen_types = set()
        
        # Check for required types
        present_types = {s.type for s in settings if s.is_enabled}
        missing_types = self.REQUIRED_TYPES - present_types
        
        if missing_types:
            errors.append(ValidationError(
                setting_id=None,
                code="MISSING_REQUIRED_TYPES",
                message=f"Missing required cost types: {', '.join(missing_types)}",
                context={"missing_types": list(missing_types)}
            ))
            
        # Check for incompatible combinations
        for setting in settings:
            if setting.type in seen_types:
                errors.append(ValidationError(
                    setting_id=setting.id,
                    code="DUPLICATE_TYPE",
                    message=f"Duplicate setting type: {setting.type}",
                    context={"type": setting.type}
                ))
            seen_types.add(setting.type)
            
            # Check incompatibilities
            if setting.type in self.INCOMPATIBLE_TYPES:
                incompatible = self.INCOMPATIBLE_TYPES[setting.type]
                conflicts = incompatible & seen_types
                if conflicts:
                    errors.append(ValidationError(
                        setting_id=setting.id,
                        code="INCOMPATIBLE_TYPES",
                        message=f"{setting.type} cannot be used with: {', '.join(conflicts)}",
                        context={
                            "type": setting.type,
                            "conflicts": list(conflicts)
                        }
                    ))
                    
        return errors

    def validate_all(self, settings: List[CostSetting]) -> List[ValidationError]:
        """
        Perform all validations on a list of settings.
        
        Args:
            settings: List of CostSettings to validate
            
        Returns:
            List of all validation errors
        """
        errors = []
        
        # Validate individual settings
        for setting in settings:
            errors.extend(self.validate_setting(setting))
            
        # Validate combinations
        errors.extend(self.validate_combinations(settings))
        
        return errors
