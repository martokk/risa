import pytest
from sqlmodel import Session

from app import crud, models
from app.crud.exceptions import RecordNotFoundError


@pytest.fixture
def context_section_data() -> dict[str, str]:
    return {"name": "Section 1", "description": "First section."}


@pytest.fixture
def another_context_section_data() -> dict[str, str]:
    return {"name": "Section 2", "description": "Second section."}


@pytest.mark.asyncio
async def test_create_context_section(db: Session, context_section_data: dict[str, str]) -> None:
    """Test creating a ContextSection."""
    obj_in = models.ContextSectionCreate(**context_section_data)
    section = await crud.context_section.create(db, obj_in=obj_in)
    assert section.id is not None
    assert section.name == context_section_data["name"]
    assert section.description == context_section_data["description"]


@pytest.mark.asyncio
async def test_get_context_section(db: Session, context_section_data: dict[str, str]) -> None:
    """Test retrieving a ContextSection by ID."""
    obj_in = models.ContextSectionCreate(**context_section_data)
    section = await crud.context_section.create(db, obj_in=obj_in)
    fetched = await crud.context_section.get(db, id=section.id)
    assert fetched is not None
    assert fetched.id == section.id
    assert fetched.name == section.name


@pytest.mark.asyncio
async def test_get_all_context_sections(
    db: Session,
    context_section_data: dict[str, str],
    another_context_section_data: dict[str, str],
) -> None:
    """Test retrieving multiple ContextSections."""
    await crud.context_section.create(
        db, obj_in=models.ContextSectionCreate(**context_section_data)
    )
    await crud.context_section.create(
        db, obj_in=models.ContextSectionCreate(**another_context_section_data)
    )
    sections = await crud.context_section.get_all(db)
    assert len(sections) >= 2
    names = [s.name for s in sections]
    assert context_section_data["name"] in names
    assert another_context_section_data["name"] in names


@pytest.mark.asyncio
async def test_update_context_section(db: Session, context_section_data: dict[str, str]) -> None:
    """Test updating a ContextSection."""
    obj_in = models.ContextSectionCreate(**context_section_data)
    section = await crud.context_section.create(db, obj_in=obj_in)
    update_in = models.ContextSectionUpdate(name="Updated Section", description="Updated desc.")
    updated = await crud.context_section.update(db, id=section.id, obj_in=update_in)
    assert updated.name == "Updated Section"
    assert updated.description == "Updated desc."


@pytest.mark.asyncio
async def test_delete_context_section(db: Session, context_section_data: dict[str, str]) -> None:
    """Test deleting a ContextSection."""
    obj_in = models.ContextSectionCreate(**context_section_data)
    section = await crud.context_section.create(db, obj_in=obj_in)
    await crud.context_section.remove(db, id=section.id)
    with pytest.raises(RecordNotFoundError):
        await crud.context_section.get(db, id=section.id)
