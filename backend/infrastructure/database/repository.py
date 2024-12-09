from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import asdict
from .models import Route as RouteModel, Offer, CostSetting
from backend.domain.entities import (
    Route, Location, EmptyDriving, MainRoute, 
    TransportType, Cargo, TimelineEvent, CountrySegment
)
from uuid import UUID
from backend.infrastructure.monitoring.performance_metrics import measure_db_query_time
import structlog
from sqlalchemy.exc import SQLAlchemyError
from functools import lru_cache
from threading import Lock

class Repository:
    def __init__(self, db: Session):
        self.db = db
        self.logger = structlog.get_logger(__name__)
        self._cost_settings_cache: Dict[str, CostSetting] = {}
        self._cache_lock = Lock()

    # Route methods
    @measure_db_query_time(query_type="create", table="routes")
    def create_route(self, route_data: Dict[str, Any]) -> RouteModel:
        route = RouteModel(**route_data)
        self.db.add(route)
        self.db.commit()
        self.db.refresh(route)
        return route

    @measure_db_query_time(query_type="save", table="routes")
    def save_route(self, route: Route) -> Route:
        """Save a route object to the database."""
        try:
            # Convert ISO format strings to datetime objects if they are strings
            pickup_time = route.pickup_time if isinstance(route.pickup_time, datetime) else datetime.fromisoformat(route.pickup_time)
            delivery_time = route.delivery_time if isinstance(route.delivery_time, datetime) else datetime.fromisoformat(route.delivery_time)

            # Use the route's to_dict method to get a JSON-serializable dictionary
            route_dict = route.to_dict()

            # Extract the required fields for the Route model
            route_model_dict = {
                "id": str(route.id),
                "origin_latitude": route.origin.latitude,
                "origin_longitude": route.origin.longitude,
                "origin_address": route.origin.address,
                "destination_latitude": route.destination.latitude,
                "destination_longitude": route.destination.longitude,
                "destination_address": route.destination.address,
                "pickup_time": pickup_time,
                "delivery_time": delivery_time,
                "total_duration_hours": route.total_duration_hours,
                "is_feasible": route.is_feasible,
                "duration_validation": route.duration_validation,
                "transport_type": route_dict.get("transport_type"),
                "cargo": route_dict.get("cargo"),
                "total_cost": route.total_cost,
                "currency": route.currency,
                "empty_driving": route_dict.get("empty_driving"),
                "main_route": route_dict.get("main_route"),
                "timeline": route_dict.get("timeline")
            }

            route_model = RouteModel(**route_model_dict)
            self.db.add(route_model)
            self.db.commit()
            self.db.refresh(route_model)
            return route

        except Exception as e:
            self.db.rollback()
            raise e

    @measure_db_query_time(query_type="get", table="routes")
    def get_route(self, route_id: UUID) -> Optional[Route]:
        """Get a route by ID. Accepts both string and UUID objects."""
        route_id_str = str(route_id)
        db_route = self.db.query(RouteModel).filter(RouteModel.id == route_id_str).first()
        if db_route:
            return self._to_domain_route(db_route)
        return None

    @measure_db_query_time(query_type="list", table="routes")
    def list_routes(self) -> List[RouteModel]:
        return self.db.query(RouteModel).all()

    # Offer methods
    @measure_db_query_time(query_type="create", table="offers")
    def create_offer(self, offer_data: Dict[str, Any]) -> Offer:
        offer = Offer(**offer_data)
        self.db.add(offer)
        self.db.commit()
        self.db.refresh(offer)
        return offer

    @measure_db_query_time(query_type="save", table="offers")
    def save_offer(self, offer: Offer) -> Offer:
        """Save an offer object to the database."""
        offer_dict = {
            "id": str(offer.id) if offer.id else None,
            "route_id": str(offer.route_id),
            "total_cost": offer.total_cost,
            "margin": offer.margin,
            "final_price": offer.final_price,
            "fun_fact": offer.fun_fact,
            "status": offer.status,
            "cost_breakdown": offer.cost_breakdown
        }
        return self.create_offer(offer_dict)

    @measure_db_query_time(query_type="get", table="offers")
    def get_offer(self, offer_id: UUID) -> Optional[Offer]:
        return self.db.query(Offer).filter(Offer.id == offer_id).first()

    @measure_db_query_time(query_type="list", table="offers")
    def list_offers(self) -> List[Offer]:
        return self.db.query(Offer).all()

    # Cost Setting methods
    @measure_db_query_time(query_type="get", table="cost_settings")
    def get_cost_setting(self, cost_setting_id: str) -> Optional[CostSetting]:
        return self.db.query(CostSetting).filter(CostSetting.id == cost_setting_id).first()

    @measure_db_query_time(query_type="list", table="cost_settings")
    def list_cost_settings(self) -> List[CostSetting]:
        return self.db.query(CostSetting).all()

    @measure_db_query_time(query_type="create", table="cost_settings")
    def create_cost_setting(self, cost_setting_data: Dict[str, Any]) -> CostSetting:
        """Create a new cost setting in the database."""
        cost_setting = CostSetting(**cost_setting_data)
        self.db.add(cost_setting)
        self.db.commit()
        self.db.refresh(cost_setting)
        return cost_setting

    @measure_db_query_time(query_type="update", table="cost_settings")
    def update_cost_setting(self, cost_setting: CostSetting) -> Optional[CostSetting]:
        """Update a cost setting in the database."""
        db_setting = self.get_cost_setting(str(cost_setting.id))
        if not db_setting:
            return None

        # Update fields directly
        for key in ['base_value', 'multiplier', 'is_enabled']:
            if hasattr(cost_setting, key):
                value = getattr(cost_setting, key)
                if value is not None:  # Only update if value is provided
                    setattr(db_setting, key, value)

        self.db.commit()
        self.db.refresh(db_setting)
        return db_setting

    @measure_db_query_time(query_type="update", table="cost_settings")
    def save_cost_settings(self, cost_settings_data: List[Dict]) -> List[CostSetting]:
        """Save multiple cost settings to the database."""
        cost_settings = []
        for data in cost_settings_data:
            # If id exists, update existing setting
            if 'id' in data:
                setting = self.get_cost_setting(data['id'])
                if setting:
                    for key, value in data.items():
                        if key != 'id' and value is not None:
                            setattr(setting, key, value)
                    cost_settings.append(setting)
                    continue

            # Create new setting if no id or setting not found
            setting = CostSetting(**data)
            self.db.add(setting)
            cost_settings.append(setting)

        self.db.commit()
        for setting in cost_settings:
            self.db.refresh(setting)
        return cost_settings

    @measure_db_query_time(query_type="update", table="cost_settings")
    def bulk_update_cost_settings(self, settings: List[CostSetting]) -> bool:
        """
        Update multiple cost settings in a single transaction.
        
        Args:
            settings: List of CostSetting objects to update
            
        Returns:
            bool: True if update was successful, False otherwise
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            self.logger.info("starting_bulk_update", count=len(settings))
            
            # Start transaction
            for setting in settings:
                self.db.merge(setting)
            
            self.db.commit()
            
            # Invalidate cache after successful update
            with self._cache_lock:
                self._cost_settings_cache.clear()
            
            self.logger.info("bulk_update_completed", count=len(settings))
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error("bulk_update_failed", error=str(e))
            raise
    
    @measure_db_query_time(query_type="read", table="cost_settings")
    def cache_cost_settings(self) -> Dict[str, CostSetting]:
        """
        Load and cache all cost settings for quick access.
        Uses thread-safe implementation with locks.
        
        Returns:
            Dict[str, CostSetting]: Dictionary of name-indexed cost settings
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            with self._cache_lock:
                # Check if cache is already populated
                if self._cost_settings_cache:
                    self.logger.info("returning_cached_settings", 
                                   count=len(self._cost_settings_cache))
                    return self._cost_settings_cache
                
                # Load settings from database
                settings = self.db.query(CostSetting).filter(
                    CostSetting.is_enabled == True
                ).all()
                
                # Update cache
                self._cost_settings_cache = {
                    setting.name: setting for setting in settings
                }
                
                self.logger.info("cost_settings_cached", 
                               count=len(self._cost_settings_cache))
                return self._cost_settings_cache
                
        except SQLAlchemyError as e:
            self.logger.error("cache_update_failed", error=str(e))
            raise
    
    @measure_db_query_time(query_type="update", table="routes")
    def atomic_update_cost_calculations(self, route_id: str, 
                                      cost_updates: Dict) -> bool:
        """
        Atomically update cost calculations for a route.
        Uses database transaction to ensure consistency.
        
        Args:
            route_id: ID of the route to update
            cost_updates: Dictionary containing cost updates
            
        Returns:
            bool: True if update was successful
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            self.logger.info("starting_atomic_update", 
                           route_id=route_id)
            
            # Start transaction
            route = self.db.query(RouteModel).filter(
                RouteModel.id == route_id
            ).with_for_update().first()
            
            if not route:
                self.logger.error("route_not_found", route_id=route_id)
                raise ValueError(f"Route not found: {route_id}")
            
            # Update route costs
            route.total_cost = cost_updates.get('total_cost')
            route.cost_breakdown = cost_updates.get('breakdown')
            route.last_cost_update = datetime.utcnow()
            
            # If there are related offers, update their costs too
            for offer in route.offers:
                offer.total_cost = cost_updates.get('total_cost')
                offer.cost_breakdown = cost_updates.get('breakdown')
                offer.last_updated = datetime.utcnow()
            
            self.db.commit()
            self.logger.info("atomic_update_completed", 
                           route_id=route_id)
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error("atomic_update_failed", 
                            route_id=route_id, 
                            error=str(e))
            raise
    
    def get_route_by_id(self, route_id: str) -> Optional[RouteModel]:
        """Get a route by its ID."""
        try:
            route = self.db.query(RouteModel).filter(
                RouteModel.id == route_id
            ).first()
            
            if route:
                self.logger.info("route_retrieved", route_id=route_id)
            else:
                self.logger.warning("route_not_found", route_id=route_id)
                
            return route
            
        except SQLAlchemyError as e:
            self.logger.error("route_retrieval_failed", 
                            route_id=route_id, 
                            error=str(e))
            raise
    
    def get_enabled_cost_settings(self) -> List[CostSetting]:
        """Get all enabled cost settings."""
        try:
            settings = self.db.query(CostSetting).filter(
                CostSetting.is_enabled == True
            ).all()
            
            self.logger.info("enabled_settings_retrieved", 
                           count=len(settings))
            return settings
            
        except SQLAlchemyError as e:
            self.logger.error("settings_retrieval_failed", error=str(e))
            raise

    def _to_domain_route(self, db_route: RouteModel) -> Route:
        """Convert database model to domain entity."""
        # Convert string to datetime if needed
        pickup_time = db_route.pickup_time if isinstance(db_route.pickup_time, datetime) else datetime.fromisoformat(db_route.pickup_time)
        delivery_time = db_route.delivery_time if isinstance(db_route.delivery_time, datetime) else datetime.fromisoformat(db_route.delivery_time)

        # Create Location objects
        origin = Location(
            latitude=db_route.origin_latitude,
            longitude=db_route.origin_longitude,
            address=db_route.origin_address
        )
        destination = Location(
            latitude=db_route.destination_latitude,
            longitude=db_route.destination_longitude,
            address=db_route.destination_address
        )

        # Create Route object with basic fields
        route = Route(
            id=UUID(db_route.id),
            origin=origin,
            destination=destination,
            pickup_time=pickup_time,
            delivery_time=delivery_time,
            total_duration_hours=db_route.total_duration_hours,
            is_feasible=db_route.is_feasible,
            duration_validation=db_route.duration_validation,
            transport_type=TransportType(**db_route.transport_type) if db_route.transport_type else None,
            cargo=Cargo(**db_route.cargo) if db_route.cargo else None
        )

        # Set route segments
        if db_route.empty_driving:
            empty_driving_data = db_route.empty_driving
            country_segments = [
                CountrySegment(**segment) 
                for segment in empty_driving_data.get('country_segments', [])
            ]
            route.empty_driving = EmptyDriving(
                distance_km=empty_driving_data.get('distance_km', 0.0),
                duration_hours=empty_driving_data.get('duration_hours', 0.0),
                base_cost=empty_driving_data.get('base_cost', 0.0),
                country_segments=country_segments
            )
            
        if db_route.main_route:
            main_route_data = db_route.main_route
            country_segments = [
                CountrySegment(**segment) 
                for segment in main_route_data.get('country_segments', [])
            ]
            route.main_route = MainRoute(
                distance_km=main_route_data.get('distance_km', 0.0),
                duration_hours=main_route_data.get('duration_hours', 0.0),
                base_cost=main_route_data.get('base_cost', 0.0),
                country_segments=country_segments
            )
            
        if db_route.timeline:
            route.timeline = [TimelineEvent(**event) for event in db_route.timeline]

        return route
