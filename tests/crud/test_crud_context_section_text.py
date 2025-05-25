from datetime import datetime

import pytest
from sqlmodel import Session

from app import crud, models
from app.crud.exceptions import RecordNotFoundError


@pytest.fixture
async def context_id(db: Session) -> int:
    context = await crud.context.create(
        db, obj_in=models.ContextCreate(template_id=None, name="Test Context")
    )
    return context.id


@pytest.fixture
async def section_id(db: Session) -> int:
    section = await crud.context_section.create(
        db, obj_in=models.ContextSectionCreate(name="Section", description="Desc")
    )
    return section.id


@pytest.fixture
def context_section_text_data(context_id: int, section_id: int) -> dict[str, int | str]:
    return {"context_id": context_id, "section_id": section_id, "text": "Initial text."}


@pytest.mark.asyncio
async def test_create_context_section_text(
    db: Session, context_section_text_data: dict[str, int | str]
) -> None:
    """Test creating a ContextSectionText."""
    obj_in = models.ContextSectionTextCreate(**context_section_text_data)
    text_obj = await crud.context_section_text.create(db, obj_in=obj_in)
    assert text_obj.id is not None
    assert text_obj.text == context_section_text_data["text"]
    assert isinstance(text_obj.created_at, datetime)
    assert isinstance(text_obj.updated_at, datetime)


@pytest.mark.asyncio
async def test_get_context_section_text(
    db: Session, context_section_text_data: dict[str, int | str]
) -> None:
    """Test retrieving a ContextSectionText by ID."""
    obj_in = models.ContextSectionTextCreate(**context_section_text_data)
    text_obj = await crud.context_section_text.create(db, obj_in=obj_in)
    fetched = await crud.context_section_text.get(db, id=text_obj.id)
    assert fetched is not None
    assert fetched.id == text_obj.id
    assert fetched.text == text_obj.text


@pytest.mark.asyncio
async def test_get_all_context_section_texts(
    db: Session, context_section_text_data: dict[str, int | str]
) -> None:
    """Test retrieving multiple ContextSectionTexts."""
    await crud.context_section_text.create(
        db, obj_in=models.ContextSectionTextCreate(**context_section_text_data)
    )
    await crud.context_section_text.create(
        db, obj_in=models.ContextSectionTextCreate(**context_section_text_data)
    )
    texts = await crud.context_section_text.get_all(db)
    assert len(texts) >= 2


@pytest.mark.asyncio
async def test_update_context_section_text(
    db: Session, context_section_text_data: dict[str, int | str]
) -> None:
    """Test updating a ContextSectionText."""
    obj_in = models.ContextSectionTextCreate(**context_section_text_data)
    text_obj = await crud.context_section_text.create(db, obj_in=obj_in)
    update_in = models.ContextSectionTextUpdate(text="Updated text.")
    updated = await crud.context_section_text.update(db, id=text_obj.id, obj_in=update_in)
    assert updated.text == "Updated text."
    assert updated.updated_at >= text_obj.updated_at


@pytest.mark.asyncio
async def test_delete_context_section_text(
    db: Session, context_section_text_data: dict[str, int | str]
) -> None:
    """Test deleting a ContextSectionText."""
    obj_in = models.ContextSectionTextCreate(**context_section_text_data)
    text_obj = await crud.context_section_text.create(db, obj_in=obj_in)
    await crud.context_section_text.remove(db, id=text_obj.id)
    with pytest.raises(RecordNotFoundError):
        await crud.context_section_text.get(db, id=text_obj.id)
