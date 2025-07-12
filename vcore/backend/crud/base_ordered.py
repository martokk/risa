from typing import Any, TypeVar

from sqlmodel import Session, SQLModel, col, select

from vcore.backend.crud.base import BaseCRUD


ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=SQLModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=SQLModel)


class BaseOrderedCRUD(BaseCRUD[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base class for CRUD operations with ordering functionality."""

    async def create(self, db: Session, *, obj_in: CreateSchemaType, **kwargs: Any) -> ModelType:
        """Create a new object and set the order to the next available order."""
        obj_in.order = await self.get_next_order(db)
        return await super().create(db, obj_in=obj_in)

    async def get_next_order(self, db: Session) -> int:
        """Get the next available order."""
        result = db.exec(
            select(self.model).order_by(col(self.model.order).desc())  # type: ignore
        ).first()
        return (result.order + 1) if result else 0  # type: ignore

    async def get_all_ordered(self, db: Session) -> list[ModelType]:
        """Get all objects ordered by order."""
        return list(db.exec(select(self.model).order_by(col(self.model.order))))  # type: ignore
