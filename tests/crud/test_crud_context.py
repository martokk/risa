import pytest
from sqlmodel import Session

from app import crud, models
from app.crud.exceptions import RecordNotFoundError


@pytest.fixture
def context_data() -> dict[str, int | None]:
    return {"template_id": 1, "name": "Test Context"}


@pytest.mark.asyncio
async def test_create_context(db: Session, context_data: dict[str, int | None]) -> None:
    """Test creating a Context."""
    obj_in = models.ContextCreate(**context_data)
    context = await crud.context.create(db, obj_in=obj_in)
    assert context.id is not None
    assert context.template_id == context_data["template_id"]


@pytest.mark.asyncio
async def test_get_context(db: Session, context_data: dict[str, int | None]) -> None:
    """Test retrieving a Context by ID."""
    obj_in = models.ContextCreate(**context_data)
    context = await crud.context.create(db, obj_in=obj_in)
    fetched = await crud.context.get(db, id=context.id)
    assert fetched is not None
    assert fetched.id == context.id
    assert fetched.template_id == context.template_id


@pytest.mark.asyncio
async def test_get_all_contexts(db: Session, context_data: dict[str, int | None]) -> None:
    """Test retrieving multiple Contexts."""
    await crud.context.create(db, obj_in=models.ContextCreate(**context_data))
    await crud.context.create(db, obj_in=models.ContextCreate(**context_data))
    contexts = await crud.context.get_all(db)
    assert len(contexts) >= 2


@pytest.mark.asyncio
async def test_update_context(db: Session, context_data: dict[str, int | None]) -> None:
    """Test updating a Context."""
    obj_in = models.ContextCreate(**context_data)
    context = await crud.context.create(db, obj_in=obj_in)
    update_in = models.ContextUpdate(template_id=2)
    updated = await crud.context.update(db, id=context.id, obj_in=update_in)
    assert updated.template_id == 2


@pytest.mark.asyncio
async def test_delete_context(db: Session, context_data: dict[str, int | None]) -> None:
    """Test deleting a Context."""
    obj_in = models.ContextCreate(**context_data)
    context = await crud.context.create(db, obj_in=obj_in)
    await crud.context.remove(db, id=context.id)
    with pytest.raises(RecordNotFoundError):
        await crud.context.get(db, id=context.id)
