from collections.abc import Generator
from typing import Any

import pytest
from sqlmodel import Field, Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.crud.base_ordered import BaseOrderedCRUD


# Test Model
class MockOrderedModel(SQLModel, table=True):
    """Test model with ordering functionality."""

    id: int = Field(primary_key=True)
    order: int = Field(default=0)
    name: str


# Test CRUD class
class MockOrderedCRUD(BaseOrderedCRUD[MockOrderedModel, MockOrderedModel, MockOrderedModel]):
    """Test CRUD class for ordered models."""

    model = MockOrderedModel

    def __init__(self) -> None:
        super().__init__(model=MockOrderedModel)


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, Any, None]:
    """Create a test database session."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def crud() -> MockOrderedCRUD:
    """Create a test CRUD instance."""
    return MockOrderedCRUD()


async def test_create_first_item(session: Session, crud: MockOrderedCRUD) -> None:
    """Test creating the first ordered item."""
    # Create first item
    item = MockOrderedModel(id=1, name="First Item")
    created_item = await crud.create(db=session, obj_in=item)

    # Check order is 0 for first item
    assert created_item.order == 0
    assert created_item.name == "First Item"


async def test_create_subsequent_items(session: Session, crud: MockOrderedCRUD) -> None:
    """Test creating multiple ordered items."""
    # Create first item
    first_item = await crud.create(db=session, obj_in=MockOrderedModel(id=1, name="First"))
    assert first_item.order == 0

    # Create second item
    second_item = await crud.create(db=session, obj_in=MockOrderedModel(id=2, name="Second"))
    assert second_item.order == 1

    # Create third item
    third_item = await crud.create(db=session, obj_in=MockOrderedModel(id=3, name="Third"))
    assert third_item.order == 2


async def test_get_next_order_empty_db(session: Session, crud: MockOrderedCRUD) -> None:
    """Test getting next order with empty database."""
    next_order = await crud.get_next_order(db=session)
    assert next_order == 0


async def test_get_next_order_with_items(session: Session, crud: MockOrderedCRUD) -> None:
    """Test getting next order with existing items."""
    # Create items with specific orders
    items = [
        MockOrderedModel(id=1, name="Item 1", order=0),
        MockOrderedModel(id=2, name="Item 2", order=1),
        MockOrderedModel(id=3, name="Item 3", order=2),
    ]
    for item in items:
        session.add(item)
    session.commit()

    next_order = await crud.get_next_order(db=session)
    assert next_order == 3


async def test_get_all_ordered(session: Session, crud: MockOrderedCRUD) -> None:
    """Test retrieving all items in order."""
    # Create items with different orders
    items = [
        MockOrderedModel(id=1, name="Item B", order=1),
        MockOrderedModel(id=2, name="Item A", order=0),
        MockOrderedModel(id=3, name="Item C", order=2),
    ]
    for item in items:
        session.add(item)
    session.commit()

    # Get ordered items
    ordered_items = await crud.get_all_ordered(db=session)

    # Check items are in correct order
    assert len(ordered_items) == 3
    assert ordered_items[0].name == "Item A"
    assert ordered_items[1].name == "Item B"
    assert ordered_items[2].name == "Item C"


async def test_create_with_custom_order(session: Session, crud: MockOrderedCRUD) -> None:
    """Test creating an item with a custom order."""
    # Create an item with a specific order
    item = MockOrderedModel(id=1, name="Custom Order", order=5)
    created_item = await crud.create(db=session, obj_in=item)

    # The order should be overridden by the next available order (0)
    assert created_item.order == 0
