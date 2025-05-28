from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock

import pytest
from sqlmodel import Field, Session, SQLModel

from app.crud.base import BaseCRUD
from app.crud.exceptions import DeleteError, RecordNotFoundError


# Test Models
class MockModel(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    description: str | None = None


class MockModelCreate(SQLModel):
    name: str
    description: str | None = None


class MockModelUpdate(SQLModel):
    name: str | None = None
    description: str | None = None


# Fixtures
@pytest.fixture
def crud() -> BaseCRUD[MockModel, MockModelCreate, MockModelUpdate]:
    """Create a BaseCRUD instance for testing."""
    return BaseCRUD[MockModel, MockModelCreate, MockModelUpdate](MockModel)


@pytest.fixture
def db_session() -> Generator[Session, Any, None]:
    """Create a mock database session."""
    session = MagicMock(spec=Session)
    yield session


@pytest.fixture
def test_model() -> MockModel:
    """Create a test model instance."""
    return MockModel(id=1, name="test", description="test description")


@pytest.fixture
def test_models() -> list[MockModel]:
    """Create a list of test model instances."""
    return [
        MockModel(id=1, name="test1", description="description1"),
        MockModel(id=2, name="test2", description="description2"),
        MockModel(id=3, name="test3", description="description3"),
    ]


# Tests
async def test_get_all(
    crud: BaseCRUD[Any, Any, Any], db_session: Session, test_models: list[MockModel]
) -> None:
    """Test getting all records."""
    db_session.exec.return_value.all.return_value = test_models  # type: ignore
    result = await crud.get_all(db_session)
    assert result == test_models
    assert len(result) == 3


async def test_get_first(
    crud: BaseCRUD[Any, Any, Any], db_session: Session, test_model: MockModel
) -> None:
    """Test getting first record."""
    db_session.exec.return_value.first.return_value = test_model  # type: ignore
    result = await crud.get_first(db_session)
    assert result == test_model


async def test_get_success(
    crud: BaseCRUD[Any, Any, Any], db_session: Session, test_model: MockModel
) -> None:
    """Test getting a record successfully."""
    db_session.exec.return_value.first.return_value = test_model  # type: ignore
    result = await crud.get(db_session, id=1)
    assert result == test_model


async def test_get_not_found(crud: BaseCRUD[Any, Any, Any], db_session: Session) -> None:
    """Test getting a non-existent record."""
    db_session.exec.return_value.first.return_value = None  # type: ignore
    with pytest.raises(RecordNotFoundError):
        await crud.get(db_session, id=999)


async def test_get_or_none_found(
    crud: BaseCRUD[Any, Any, Any], db_session: Session, test_model: MockModel
) -> None:
    """Test get_or_none when record exists."""
    db_session.exec.return_value.first.return_value = test_model  # type: ignore
    result = await crud.get_or_none(db_session, id=1)
    assert result == test_model


async def test_get_or_none_not_found(crud: BaseCRUD[Any, Any, Any], db_session: Session) -> None:
    """Test get_or_none when record doesn't exist."""
    db_session.exec.return_value.first.return_value = None  # type: ignore
    result = await crud.get_or_none(db_session, id=999)
    assert result is None


async def test_get_multi(
    crud: BaseCRUD[Any, Any, Any], db_session: Session, test_models: list[MockModel]
) -> None:
    """Test getting multiple records."""
    db_session.exec.return_value.fetchmany.return_value = test_models[:2]  # type: ignore
    result = await crud.get_all(db_session, skip=0, limit=2)
    assert result == test_models[:2]
    assert len(result) == 2


async def test_create_success(
    crud: BaseCRUD[Any, Any, Any], db_session: Session, test_model: MockModel
) -> None:
    """Test creating a record successfully."""
    db_session.refresh = MagicMock()  # type: ignore
    create_data = MockModelCreate(name="test", description="test description")
    db_session.add = MagicMock()  # type: ignore
    db_session.commit = MagicMock()  # type: ignore
    db_session.refresh = MagicMock()  # type: ignore

    result = await crud.create(db_session, obj_in=create_data)
    assert isinstance(result, MockModel)
    assert result.name == "test"
    assert result.description == "test description"
    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once()


async def test_update_success(
    crud: BaseCRUD[Any, Any, Any], db_session: Session, test_model: MockModel
) -> None:
    """Test updating a record successfully."""
    db_session.exec.return_value.first.return_value = test_model  # type: ignore
    update_data = MockModelUpdate(name="updated")

    result = await crud.update(db_session, id=1, obj_in=update_data)
    assert result.name == "updated"
    assert result.description == "test description"  # Unchanged
    db_session.commit.assert_called_once()  # type: ignore
    db_session.refresh.assert_called_once()  # type: ignore


async def test_update_not_found(crud: BaseCRUD[Any, Any, Any], db_session: Session) -> None:
    """Test updating a non-existent record."""
    db_session.exec.return_value.first.return_value = None  # type: ignore
    update_data = MockModelUpdate(name="updated")

    with pytest.raises(RecordNotFoundError):
        await crud.update(db_session, id=999, obj_in=update_data)


async def test_update_no_filter(crud: BaseCRUD[Any, Any, Any], db_session: Session) -> None:
    """Test updating without providing filters or db_obj."""
    update_data = MockModelUpdate(name="updated")

    with pytest.raises(ValueError, match="Must provide at least one filter or db_obj"):
        await crud.update(db_session, obj_in=update_data)


async def test_remove_success(
    crud: BaseCRUD[Any, Any, Any], db_session: Session, test_model: MockModel
) -> None:
    """Test removing a record successfully."""
    db_session.exec.return_value.first.return_value = test_model  # type: ignore

    await crud.remove(db_session, id=1)
    db_session.delete.assert_called_once_with(test_model)  # type: ignore
    db_session.commit.assert_called_once()  # type: ignore


async def test_remove_error(
    crud: BaseCRUD[Any, Any, Any], db_session: Session, test_model: MockModel
) -> None:
    """Test error while removing a record."""
    db_session.exec.return_value.first.return_value = test_model  # type: ignore
    db_session.commit.side_effect = Exception("Delete error")  # type: ignore

    with pytest.raises(DeleteError):
        await crud.remove(db_session, id=1)


async def test_count(crud: BaseCRUD[Any, Any, Any], db_session: Session) -> None:
    """Test counting records."""
    db_session.exec.return_value.scalar.return_value = 3  # type: ignore

    result = await crud.count(db_session)
    assert result == 3


async def test_count_no_records(crud: BaseCRUD[Any, Any, Any], db_session: Session) -> None:
    """Test counting when no records exist."""
    db_session.exec.return_value.scalar.return_value = None  # type: ignore

    result = await crud.count(db_session)
    assert result == 0
