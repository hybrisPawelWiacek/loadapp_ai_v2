from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID
import structlog

from ..entities.cost_setting import CostSetting
from ..validators.cost_setting_validator import CostSettingValidator, ValidationError
from backend.infrastructure.database.repositories.cost_setting_repository import CostSettingsRepository
from backend.infrastructure.monitoring.metrics_service import MetricsService

class CostSettingsService:
    """Service for managing cost settings."""

    def __init__(
        self,
        repository: CostSettingsRepository,
        validator: CostSettingValidator,
        metrics_service: MetricsService
    ):
        """Initialize the cost settings service."""
        self.repository = repository
        self.validator = validator
        self.metrics_service = metrics_service
        self.logger = structlog.get_logger(__name__)

    def get_all_settings(self) -> List[CostSetting]:
        """
        Retrieve all cost settings.
        
        Returns:
            List of all cost settings
        """
        try:
            # Initialize default settings if none exist
            self.repository.initialize_default_settings()
            
            settings = self.repository.get_all_cost_settings()
            self.metrics_service.gauge(
                "cost_settings.total_count",
                len(settings)
            )
            return settings
        except Exception as e:
            self.logger.error("failed_to_get_settings", error=str(e))
            raise

    def update_settings(self, settings: List[CostSetting]) -> Dict:
        """
        Update multiple cost settings after validation.
        
        Args:
            settings: List of settings to update
            
        Returns:
            Dictionary containing update results and any validation errors
            
        Raises:
            ValueError: If validation fails with critical errors
        """
        try:
            # Validate all settings
            validation_errors = self.validator.validate_all(settings)
            
            # Separate errors by severity
            critical_errors = [e for e in validation_errors if e.severity == "error"]
            warnings = [e for e in validation_errors if e.severity == "warning"]
            
            # Track validation metrics
            self.metrics_service.gauge(
                "cost_settings.validation.error_count",
                len(critical_errors)
            )
            self.metrics_service.gauge(
                "cost_settings.validation.warning_count",
                len(warnings)
            )
            
            # If there are critical errors, don't proceed with update
            if critical_errors:
                self.metrics_service.increment("cost_settings.validation_failures")
                return {
                    "success": False,
                    "errors": [
                        {
                            "setting_id": str(e.setting_id) if e.setting_id else None,
                            "code": e.code,
                            "message": e.message,
                            "context": e.context
                        }
                        for e in critical_errors
                    ],
                    "warnings": [
                        {
                            "setting_id": str(e.setting_id) if e.setting_id else None,
                            "code": e.code,
                            "message": e.message,
                            "context": e.context
                        }
                        for e in warnings
                    ]
                }
            
            # Proceed with update
            start_time = datetime.utcnow()
            success = self.repository.update_cost_settings(settings)
            
            # Track metrics
            update_duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics_service.timing(
                "cost_settings.update_duration",
                update_duration
            )
            
            if success:
                self.metrics_service.increment("cost_settings.successful_updates")
                self.logger.info("settings_updated_successfully",
                               count=len(settings),
                               warning_count=len(warnings))
                
                return {
                    "success": True,
                    "updated_count": len(settings),
                    "warnings": [
                        {
                            "setting_id": str(e.setting_id) if e.setting_id else None,
                            "code": e.code,
                            "message": e.message,
                            "context": e.context
                        }
                        for e in warnings
                    ],
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                self.metrics_service.increment("cost_settings.failed_updates")
                self.logger.error("failed_to_update_settings")
                return {
                    "success": False,
                    "errors": [{
                        "code": "UPDATE_FAILED",
                        "message": "Failed to update settings in database"
                    }],
                    "warnings": [
                        {
                            "setting_id": str(e.setting_id) if e.setting_id else None,
                            "code": e.code,
                            "message": e.message,
                            "context": e.context
                        }
                        for e in warnings
                    ]
                }
                
        except Exception as e:
            self.metrics_service.increment("cost_settings.update_errors")
            self.logger.error("update_settings_error", error=str(e))
            raise

    def validate_settings(self, settings: List[CostSetting]) -> List[ValidationError]:
        """
        Validate a list of cost settings.
        
        Args:
            settings: List of settings to validate
            
        Returns:
            List of validation results
        """
        try:
            results = self.validator.validate_settings(settings)
            
            # Track validation metrics
            valid_count = sum(1 for r in results if r.is_valid)
            self.metrics_service.gauge(
                "cost_settings.validation_success_rate",
                valid_count / len(settings) if settings else 0
            )
            
            return results
        except Exception as e:
            self.logger.error("validation_error", error=str(e))
            raise

    def get_default_settings(self) -> List[CostSetting]:
        """
        Get a list of default cost settings.
        
        Returns:
            List of default cost settings
        """
        try:
            # Static list of default settings
            defaults = [
                CostSetting(
                    name="Base Fuel Cost",
                    type="fuel",
                    category="variable",
                    base_value=1.5,
                    multiplier=1.0,
                    currency="EUR",
                    description="Base cost per kilometer for fuel consumption"
                ),
                CostSetting(
                    name="Standard Maintenance",
                    type="maintenance",
                    category="variable",
                    base_value=0.3,
                    multiplier=1.0,
                    currency="EUR",
                    description="Standard maintenance cost per kilometer"
                ),
                CostSetting(
                    name="Time-based Cost",
                    type="time",
                    category="variable",
                    base_value=35.0,
                    multiplier=1.0,
                    currency="EUR",
                    description="Cost per hour of transport time"
                ),
                CostSetting(
                    name="Weight-based Cost",
                    type="weight",
                    category="cargo-specific",
                    base_value=0.1,
                    multiplier=1.0,
                    currency="EUR",
                    description="Cost per kilogram of cargo"
                )
            ]
            
            self.metrics_service.gauge(
                "cost_settings.default_settings_count",
                len(defaults)
            )
            
            return defaults
            
        except Exception as e:
            self.logger.error("default_settings_error", error=str(e))
            raise

    def analyze_setting_impact(
        self, setting: CostSetting
    ) -> Dict[str, float]:
        """
        Analyze the potential impact of a cost setting change.
        
        Args:
            setting: Cost setting to analyze
            
        Returns:
            Dictionary containing impact analysis metrics
        """
        try:
            # Placeholder implementation
            # In a real implementation, this would:
            # 1. Analyze historical route data
            # 2. Calculate cost differences
            # 3. Project future impact
            
            impact_analysis = {
                "average_cost_change": 0.0,  # Average change in total cost
                "affected_routes_percent": 0.0,  # Percentage of routes affected
                "monthly_cost_impact": 0.0,  # Projected monthly cost impact
                "confidence_score": 0.0  # Confidence in the analysis (0-1)
            }
            
            self.metrics_service.gauge(
                "cost_settings.impact_analysis_performed",
                1,
                labels={"setting_type": setting.type}
            )
            
            return impact_analysis
            
        except Exception as e:
            self.logger.error("impact_analysis_error",
                            setting_id=str(setting.id),
                            error=str(e))
            raise
