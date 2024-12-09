from typing import TypeVar, Generic, Type, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

T = TypeVar('T')

class BaseRepository(Generic[T]):
    def __init__(self, session: Session, model_class: Type[T]):
        self.session = session
        self.model_class = model_class

    def get_by_id(self, id: str) -> Optional[T]:
        return self.session.query(self.model_class).filter(self.model_class.id == id).first()

    def get_all(self) -> List[T]:
        return self.session.query(self.model_class).all()

    def create(self, data: Dict[str, Any]) -> T:
        instance = self.model_class(**data)
        self.session.add(instance)
        self.session.commit()
        return instance

    def update(self, id: str, data: Dict[str, Any]) -> Optional[T]:
        instance = self.get_by_id(id)
        if instance:
            for key, value in data.items():
                setattr(instance, key, value)
            self.session.commit()
        return instance

    def delete(self, id: str) -> bool:
        instance = self.get_by_id(id)
        if instance:
            self.session.delete(instance)
            self.session.commit()
            return True
        return False

    def filter_by(self, **kwargs) -> List[T]:
        return self.session.query(self.model_class).filter_by(**kwargs).all()

    def count(self) -> int:
        return self.session.query(self.model_class).count()

    def exists(self, id: str) -> bool:
        return self.session.query(
            self.session.query(self.model_class).filter_by(id=id).exists()
        ).scalar()
