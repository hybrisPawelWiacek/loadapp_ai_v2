from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_

from backend.domain.entities.cost_setting import CostSetting as CostSettingEntity
from backend.domain.entities.time_range import TimeRange
from backend.domain.entities.usage_data import UsageData
from backend.infrastructure.database.models import CostSettingModel
from backend.infrastructure.logging import logger

class CostSettingsRepository:
    """Repository for managing cost settings in the database."""

    def __init__(self, session: Session):
        self.session = session
        self.logger = logger.bind(repository="CostSettingsRepository")

    def _to_entity(self, model: CostSettingModel) -> CostSettingEntity:
        """Convert database model to domain entity."""
        return CostSettingEntity(
            id=model.id,  # Keep as UUID
            name=model.name,
            type=model.type,
            category=model.category,
            base_value=model.value,
            multiplier=model.multiplier,
            currency=model.currency,
            is_enabled=model.is_enabled,
            description=model.description,
            last_updated=model.last_updated
        )

    def _to_model(self, entity: CostSettingEntity) -> CostSettingModel:
        """Convert domain entity to database model."""
        return CostSettingModel(
            id=entity.id,  # Keep as UUID
            name=entity.name,
            type=entity.type,
            category=entity.category,
            value=entity.base_value,
            multiplier=entity.multiplier,
            currency=entity.currency,
            is_enabled=entity.is_enabled,
            description=entity.description,
            last_updated=entity.last_updated
        )

    def get_all_cost_settings(self) -> List[CostSettingEntity]:
        """Retrieve all cost settings from the database."""
        try:
            # First check if we have any settings
            settings = self.session.query(CostSettingModel).all()
            
            # If no settings exist, initialize default ones
            if not settings:
                self.initialize_default_settings()
                settings = self.session.query(CostSettingModel).all()
            
            return [self._to_entity(model) for model in settings]
        except SQLAlchemyError as e:
            self.logger.error("failed_to_get_all_settings", error=str(e))
            raise

    def get_enabled_cost_settings(self) -> List[CostSettingEntity]:
        """Retrieve only enabled cost settings."""
        try:
            models = self.session.query(CostSettingModel).filter(CostSettingModel.is_enabled == True).all()
            return [self._to_entity(model) for model in models]
        except SQLAlchemyError as e:
            self.logger.error("failed_to_get_enabled_settings", error=str(e))
            raise

    def update_cost_settings(self, settings: List[CostSettingEntity]) -> bool:
        """Update multiple cost settings in a single transaction."""
        try:
            with self.session.begin_nested():
                for setting in settings:
                    model = self.session.query(CostSettingModel).get(setting.id)  # Keep as UUID
                    if model is None:
                        self.logger.warning("setting_not_found", setting_id=str(setting.id))
                        continue
                    
                    # Update model fields
                    for key, value in setting.to_dict().items():
                        if hasattr(model, key):
                            setattr(model, key, value)
                    
                    model.last_updated = datetime.utcnow()
                    self.session.merge(model)
            
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.logger.error("failed_to_update_settings", error=str(e))
            self.session.rollback()
            raise

    def get_cost_setting_by_type(self, type: str) -> Optional[CostSettingEntity]:
        """Retrieve a cost setting by its type."""
        try:
            model = self.session.query(CostSettingModel).filter(CostSettingModel.type == type).first()
            return self._to_entity(model) if model else None
        except SQLAlchemyError as e:
            self.logger.error("failed_to_get_setting_by_type", type=type, error=str(e))
            raise

    def get_historical_data(self, setting_id: UUID, time_range: TimeRange) -> List[Dict]:
        """Get historical data for a cost setting within a specified time range.
        
        Args:
            setting_id: UUID of the cost setting
            time_range: TimeRange object specifying the query period
            
        Returns:
            List of dictionaries containing historical cost data
        """
        try:
            historical_items = (
                self.session.query(CostSettingModel)
                .filter(
                    and_(
                        CostSettingModel.id == str(setting_id),
                        CostSettingModel.created_at >= time_range.start_time,
                        CostSettingModel.created_at <= time_range.end_time
                    )
                )
                .order_by(CostSettingModel.created_at)
                .all()
            )
            
            return [
                {
                    "timestamp": item.created_at,
                    "value": item.value,
                    "metadata": item.validation_rules
                }
                for item in historical_items
            ]
            
        except SQLAlchemyError as e:
            logger.error("get_historical_data_error", 
                        error=str(e), 
                        setting_id=setting_id,
                        start_time=time_range.start_time,
                        end_time=time_range.end_time)
            raise

    def track_setting_usage(self, setting_id: UUID, usage_data: UsageData) -> None:
        """Track usage information for a specific setting.
        
        Args:
            setting_id: UUID of the cost setting to track
            usage_data: UsageData instance containing usage information
        """
        try:
            with self.session.begin_nested():
                model = self.session.query(CostSettingModel).get(str(setting_id))
                if not model:
                    logger.warning("setting_not_found_for_tracking", 
                                setting_id=str(setting_id))
                    return

                # Initialize historical data if empty
                if not model.historical_data:
                    model.historical_data = {'history': []}

                # Add new usage data
                model.historical_data['history'].append(usage_data.to_dict())
                
                # Update last used timestamp
                model.last_used = usage_data.timestamp
                
                self.session.add(model)
                self.session.commit()
                
                logger.info("usage_tracked_successfully",
                          setting_id=str(setting_id),
                          timestamp=usage_data.timestamp,
                          value=usage_data.value)
                
        except SQLAlchemyError as e:
            logger.error("track_usage_error",
                       setting_id=str(setting_id),
                       error=str(e))
            raise

    def get_by_type(self, cost_type: str) -> Optional[CostSettingModel]:
        """Get a cost setting by its type."""
        return self.session.query(CostSettingModel).filter(CostSettingModel.type == cost_type).first()
    
    def get_by_category(self, category: str) -> List[CostSettingModel]:
        """Get all cost settings in a category."""
        return self.session.query(CostSettingModel).filter(CostSettingModel.category == category).all()
    
    def get_enabled(self) -> List[CostSettingModel]:
        """Get all enabled cost settings."""
        return self.session.query(CostSettingModel).filter(CostSettingModel.is_enabled == True).all()
    
    def update_value(self, cost_id: str, new_value: float) -> Optional[CostSettingModel]:
        """Update the value of a cost setting."""
        cost_setting = self.get_by_id(cost_id)
        if cost_setting:
            cost_setting.value = new_value
            self.session.commit()
        return cost_setting
    
    def update_multiplier(self, cost_id: str, new_multiplier: float) -> Optional[CostSettingModel]:
        """Update the multiplier of a cost setting."""
        cost_setting = self.get_by_id(cost_id)
        if cost_setting:
            cost_setting.multiplier = new_multiplier
            self.session.commit()
        return cost_setting
    
    def toggle_enabled(self, cost_id: str) -> Optional[CostSettingModel]:
        """Toggle the enabled status of a cost setting."""
        cost_setting = self.get_by_id(cost_id)
        if cost_setting:
            cost_setting.is_enabled = not cost_setting.is_enabled
            self.session.commit()
        return cost_setting

    def initialize_default_settings(self) -> None:
        """Initialize default cost settings if none exist."""
        try:
            # Create default settings
            default_settings = [
                CostSettingModel(
                    id=uuid4(),
                    name="Base Distance Cost",
                    type="distance",
                    category="transport",
                    value=1.5,  # €/km
                    multiplier=1.0,
                    currency="EUR",
                    is_enabled=True,
                    description="Base cost per kilometer traveled"
                ),
                CostSettingModel(
                    id=uuid4(),
                    name="Base Time Cost",
                    type="time",
                    category="transport",
                    value=50.0,  # €/hour
                    multiplier=1.0,
                    currency="EUR",
                    is_enabled=True,
                    description="Base cost per hour of transport"
                ),
                CostSettingModel(
                    id=uuid4(),
                    name="Toll Cost",
                    type="toll",
                    category="transport",
                    value=1.0,
                    multiplier=1.0,
                    currency="EUR",
                    is_enabled=True,
                    description="Toll costs for transport routes"
                )
            ]
            
            # Add all default settings
            for setting in default_settings:
                self.session.add(setting)
            self.session.commit()
            
            self.logger.info("default_settings_initialized", count=len(default_settings))
        except SQLAlchemyError as e:
            self.logger.error("failed_to_initialize_default_settings", error=str(e))
            self.session.rollback()
            raise
