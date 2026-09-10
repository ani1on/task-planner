from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(
        self,
        db: Session,
        model: type[ModelType],
    ) -> None:
        self.db = db
        self.model = model

    def get_by_id(
        self,
        object_id: int,
    ) -> ModelType | None:
        statement = select(self.model).where(self.model.id == object_id)

        return self.db.scalar(statement)

    def create(
        self,
        obj: ModelType,
    ) -> ModelType:
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)

        return obj

    def delete(
        self,
        obj: ModelType,
    ) -> None:
        self.db.delete(obj)
        self.db.flush()
