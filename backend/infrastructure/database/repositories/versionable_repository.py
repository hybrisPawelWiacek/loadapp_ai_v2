from typing import Type, TypeVar, Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID
import logging

from .base_repository import BaseRepository
from ..models.base_version import BaseVersionModel

T = TypeVar('T')
V = TypeVar('V', bound=BaseVersionModel)

class VersionableRepository(BaseRepository[T]):
    """Repository for entities that support versioning."""
    
    def __init__(
        self, 
        session: Session,
        model_class: Type[T],
        version_model_class: Type[V]
    ):
        super().__init__(session, model_class)
        self.version_model_class = version_model_class
        self.logger = logging.getLogger(__name__)
        
    def create_version(self, version_data: dict) -> None:
        """Create a new version record for an entity.
        
        Args:
            version_data: Dictionary containing version data with keys:
                - id: UUID of the version record
                - entity_id: UUID of the entity being versioned
                - version: Integer version number
                - data: JSON data representing the entity state
                - created_at: DateTime when version was created
                - created_by: String identifier of who created the version
                - change_reason: Optional string explaining why version was created
                - version_metadata: Optional dict of additional metadata
        """
        try:
            version_model = self.version_model_class(
                id=version_data['id'],
                entity_id=version_data['entity_id'],
                version=version_data['version'],
                data=version_data['data'],
                created_at=version_data.get('created_at', datetime.utcnow()),
                created_by=version_data['created_by'],
                change_reason=version_data.get('change_reason'),
                version_metadata=version_data.get('version_metadata', {})
            )
            self.session.add(version_model)
            self.session.commit()
            
            self.logger.info(
                f"{self.model_class.__name__}_version_created",
                extra={
                    'entity_id': str(version_data['entity_id']),
                    'version': version_data['version']
                }
            )
            
        except Exception as e:
            self.session.rollback()
            self.logger.error(
                f"{self.model_class.__name__}_version_creation_failed",
                extra={
                    'error': str(e),
                    'entity_id': str(version_data['entity_id'])
                }
            )
            raise
            
    def get_versions(
        self, 
        entity_id: UUID,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[V]:
        """Get version history for an entity.
        
        Args:
            entity_id: UUID of the entity to get versions for
            limit: Optional maximum number of versions to return
            offset: Optional number of versions to skip
            
        Returns:
            List of version models, ordered by version number descending
        """
        query = (
            self.session.query(self.version_model_class)
            .filter(self.version_model_class.entity_id == entity_id)
            .order_by(self.version_model_class.version.desc())
        )
        
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
            
        return query.all()
        
    def get_version(
        self,
        entity_id: UUID,
        version: int
    ) -> Optional[V]:
        """Get a specific version of an entity.
        
        Args:
            entity_id: UUID of the entity
            version: Version number to retrieve
            
        Returns:
            Version model if found, None otherwise
        """
        return (
            self.session.query(self.version_model_class)
            .filter(
                self.version_model_class.entity_id == entity_id,
                self.version_model_class.version == version
            )
            .first()
        )
        
    def get_latest_version(
        self,
        entity_id: UUID
    ) -> Optional[V]:
        """Get the latest version of an entity.
        
        Args:
            entity_id: UUID of the entity
            
        Returns:
            Latest version model if found, None otherwise
        """
        return (
            self.session.query(self.version_model_class)
            .filter(self.version_model_class.entity_id == entity_id)
            .order_by(self.version_model_class.version.desc())
            .first()
        )
