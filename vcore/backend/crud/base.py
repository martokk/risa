from typing import Any, Generic, TypeVar

from sqlalchemy import select as sa_select
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy.sql.expression import func
from sqlmodel import Session, SQLModel, select

from app import logger
from vcore.backend.crud.exceptions import DeleteError, RecordNotFoundError


ModelType = TypeVar("ModelType", bound=SQLModel)
ModelCreateType = TypeVar("ModelCreateType", bound=SQLModel)
ModelUpdateType = TypeVar("ModelUpdateType", bound=SQLModel)


class BaseCrudMixin(Generic[ModelType, ModelCreateType, ModelUpdateType]):
    """Base mixin class for CRUD operations."""

    def __init__(self, model: type[ModelType]) -> None:
        """
        Initialize the CRUD object.

        Args:
            model: The model class to operate on.
        """
        self._model: type[ModelType] = model

    @property
    def model(self) -> type[ModelType]:
        """Get the model class."""
        return self._model

    def _get_all(self, db: Session) -> list[ModelType]:
        """
        Get all records for the model.

        Args:
            db (Session): The database session.

        Returns:
            A list of all records, or None if there are none.
        """
        statement = select(self.model)
        return list(db.exec(statement).all())

    def _get_first(self, db: Session) -> ModelType | None:
        """
        Get the first record from the table.

        Args:
            db (Session): The database session.

        Returns:
            The first record, or None if the table is empty.
        """
        statement = select(self.model)
        return db.exec(statement).first()

    def _get(self, db: Session, *args: BinaryExpression[Any], **kwargs: Any) -> ModelType:
        """
        Get a record by its primary key(s).

        Args:
            db (Session): The database session.
            args: Binary expressions to filter by.
            kwargs: Keyword arguments to filter by.

        Returns:
            The matching record.

        Raises:
            RecordNotFoundError: If no matching record is found.
        """
        statement = select(self.model).filter(*args).filter_by(**kwargs)

        result = db.exec(statement).first()
        if result is None:
            raise RecordNotFoundError(
                f"{self.model.__name__}({args=} {kwargs=}) not found in database"
            )
        return result

    def _get_or_none(
        self, db: Session, *args: BinaryExpression[Any], **kwargs: Any
    ) -> ModelType | None:
        """
        Get a record by its primary key(s), or return None if no matching record is found.

        Args:
            db (Session): The database session.
            args: Binary expressions to filter by.
            kwargs: Keyword arguments to filter by.

        Returns:
            The matching record, or None.
        """
        try:
            result = self._get(db, *args, **kwargs)
        except RecordNotFoundError:
            return None
        return result

    def _get_multi(
        self,
        db: Session,
        *args: BinaryExpression[Any],
        skip: int = 0,
        limit: int = 999999,
        **kwargs: Any,
    ) -> list[ModelType]:
        """
        Retrieve multiple rows from the database that match the given criteria.

        Args:
            db (Session): The database session.
            skip: The number of rows to skip.
            limit: The maximum number of rows to return.
            args: Binary expressions used to filter the rows to be retrieved.
            kwargs: Keyword arguments used to filter the rows to be retrieved.

        Returns:
            A list of records that match the given criteria.
        """
        statement = select(self.model).filter(*args).filter_by(**kwargs).offset(skip).limit(limit)
        return list(db.exec(statement).fetchmany())

    def _create(self, db: Session, *, obj_in: ModelCreateType, **kwargs: Any) -> ModelType:
        """
        Create a new record.

        Args:
            db (Session): The database session.
            obj_in: The object to create.

        Returns:
            The created object.

        Raises:
            RecordAlreadyExistsError: If the record already exists.
        """
        try:
            out_obj = self.model(**{**obj_in.model_dump(), **kwargs})
            db.add(out_obj)
            db.commit()
            db.refresh(out_obj)
            return out_obj
        except Exception as e:
            logger.error(f"Error in create: {str(e)}")
            db.rollback()
            raise

    def _update(
        self,
        db: Session,
        *args: BinaryExpression[Any],
        obj_in: ModelUpdateType,
        db_obj: ModelType | None = None,
        exclude_none: bool = False,
        exclude_unset: bool = True,
        **kwargs: Any,
    ) -> ModelType:
        """
        Update an existing record.

        Args:
            obj_in (ModelUpdateType): The updated object.
            args (BinaryExpression): Binary expressions to filter by.
            db (Session): The database session.
            db_obj (ModelType | None): Optional existing database object to update.
            exclude_none (bool): Whether to exclude None values from the update.
            exclude_unset (bool): Whether to exclude unset values from the update.
            kwargs (Any): Keyword arguments to filter by.

        Returns:
            The updated object.

        Raises:
            ValueError: If no filters are provided and no db_obj is passed.
        """
        if db_obj is None:
            if not args and not kwargs:
                raise ValueError("crud.base.update() Must provide at least one filter or db_obj")
            db_obj = self._get(db, *args, **kwargs)

        obj_in_values = obj_in.model_dump(exclude_unset=exclude_unset, exclude_none=exclude_none)
        db_obj_values = db_obj.model_dump()
        for obj_in_key, obj_in_value in obj_in_values.items():
            if obj_in_value != db_obj_values[obj_in_key]:
                setattr(db_obj, obj_in_key, obj_in_value)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def _remove(self, db: Session, *args: BinaryExpression[Any], **kwargs: Any) -> None:
        """
        Delete a record.

        Args:
            db (Session): The database session.
            args: Binary expressions to filter by.
            kwargs: Keyword arguments to filter by.

        Raises:
            DeleteError: If an error occurs while deleting the record.
        """
        db_obj = self._get(db, *args, **kwargs)
        try:
            db.delete(db_obj)
            db.commit()
        except Exception as exc:
            raise DeleteError("Error while deleting") from exc

    def _count(self, db: Session, *args: BinaryExpression[Any], **kwargs: Any) -> int:
        """
        Get the total count of records for the model.

        Args:
            db (Session): The database session.
            args: Binary expressions to filter by.
            kwargs: Keyword arguments to filter by.

        Returns:
            A count of records.
        """
        query = sa_select(func.count()).select_from(self.model).filter(*args).filter_by(**kwargs)
        result = db.exec(query).scalar() or 0  # type: ignore
        return result


class BaseCRUDSync(BaseCrudMixin[ModelType, ModelCreateType, ModelUpdateType]):
    """Synchronous CRUD operations."""

    def get_all(self, db: Session) -> list[ModelType]:
        return self._get_all(db)

    def get_first(self, db: Session) -> ModelType | None:
        return self._get_first(db)

    def get(self, db: Session, *args: BinaryExpression[Any], **kwargs: Any) -> ModelType:
        return self._get(db, *args, **kwargs)

    def get_or_none(
        self, db: Session, *args: BinaryExpression[Any], **kwargs: Any
    ) -> ModelType | None:
        return self._get_or_none(db, *args, **kwargs)

    def get_multi(
        self,
        db: Session,
        *args: BinaryExpression[Any],
        skip: int = 0,
        limit: int = 999999,
        **kwargs: Any,
    ) -> list[ModelType]:
        return self._get_multi(db, *args, skip=skip, limit=limit, **kwargs)

    def create(self, db: Session, *, obj_in: ModelCreateType, **kwargs: Any) -> ModelType:
        return self._create(db, obj_in=obj_in, **kwargs)

    def update(
        self,
        db: Session,
        *args: BinaryExpression[Any],
        obj_in: ModelUpdateType,
        db_obj: ModelType | None = None,
        exclude_none: bool = False,
        exclude_unset: bool = True,
        **kwargs: Any,
    ) -> ModelType:
        return self._update(
            db,
            *args,
            obj_in=obj_in,
            db_obj=db_obj,
            exclude_none=exclude_none,
            exclude_unset=exclude_unset,
            **kwargs,
        )

    def remove(self, db: Session, *args: BinaryExpression[Any], **kwargs: Any) -> None:
        return self._remove(db, *args, **kwargs)

    def count(self, db: Session, *args: BinaryExpression[Any], **kwargs: Any) -> int:
        return self._count(db, *args, **kwargs)


class BaseCRUD(BaseCrudMixin[ModelType, ModelCreateType, ModelUpdateType]):
    """Asynchronous CRUD operations with sync access."""

    def __init__(
        self,
        model: type[ModelType],
        model_crud_sync: BaseCRUDSync[ModelType, ModelCreateType, ModelUpdateType] | None = None,
    ) -> None:
        super().__init__(model=model)
        self._sync: BaseCRUDSync[ModelType, ModelCreateType, ModelUpdateType] | None = (
            model_crud_sync if model_crud_sync else None
        )

    @property
    def sync(self) -> BaseCRUDSync[ModelType, ModelCreateType, ModelUpdateType]:
        """Access synchronous operations."""
        if self._sync is None:
            self._sync = BaseCRUDSync(model=self.model)
        return self._sync

    async def get_all(self, db: Session) -> list[ModelType]:
        return self._get_all(db)

    async def get_first(self, db: Session) -> ModelType | None:
        return self._get_first(db)

    async def get(self, db: Session, *args: BinaryExpression[Any], **kwargs: Any) -> ModelType:
        return self._get(db, *args, **kwargs)

    async def get_or_none(
        self, db: Session, *args: BinaryExpression[Any], **kwargs: Any
    ) -> ModelType | None:
        return self._get_or_none(db, *args, **kwargs)

    async def get_multi(
        self,
        db: Session,
        *args: BinaryExpression[Any],
        skip: int = 0,
        limit: int = 999999,
        **kwargs: Any,
    ) -> list[ModelType]:
        return self._get_multi(db, *args, skip=skip, limit=limit, **kwargs)

    async def create(self, db: Session, *, obj_in: ModelCreateType, **kwargs: Any) -> ModelType:
        return self._create(db, obj_in=obj_in, **kwargs)

    async def update(
        self,
        db: Session,
        *args: BinaryExpression[Any],
        obj_in: ModelUpdateType,
        db_obj: ModelType | None = None,
        exclude_none: bool = False,
        exclude_unset: bool = True,
        **kwargs: Any,
    ) -> ModelType:
        return self._update(
            db,
            *args,
            obj_in=obj_in,
            db_obj=db_obj,
            exclude_none=exclude_none,
            exclude_unset=exclude_unset,
            **kwargs,
        )

    async def remove(self, db: Session, *args: BinaryExpression[Any], **kwargs: Any) -> None:
        return self._remove(db, *args, **kwargs)

    async def count(self, db: Session, *args: BinaryExpression[Any], **kwargs: Any) -> int:
        return self._count(db, *args, **kwargs)
