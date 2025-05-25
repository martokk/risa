from datetime import datetime

import pytest
from sqlmodel import Session

from app import crud, models
from app.crud.exceptions import RecordNotFoundError


@pytest.fixture
def context_template_data() -> dict[str, str]:
    return {"name": "Test Template", "description": "A template for testing."}


@pytest.fixture
def another_context_template_data() -> dict[str, str]:
    return {"name": "Another Template", "description": "Another template for testing."}


@pytest.mark.asyncio
async def test_create_context_template(db: Session, context_template_data: dict[str, str]) -> None:
    """Test creating a ContextTemplate."""
    obj_in = models.ContextTemplateCreate(**context_template_data)
    template = await crud.context_template.create(db, obj_in=obj_in)
    assert template.id is not None
    assert template.name == context_template_data["name"]
    assert template.description == context_template_data["description"]
    assert isinstance(template.created_at, datetime)
    assert isinstance(template.updated_at, datetime)


@pytest.mark.asyncio
async def test_get_context_template(db: Session, context_template_data: dict[str, str]) -> None:
    """Test retrieving a ContextTemplate by ID."""
    obj_in = models.ContextTemplateCreate(**context_template_data)
    template = await crud.context_template.create(db, obj_in=obj_in)
    fetched = await crud.context_template.get(db, id=template.id)
    assert fetched is not None
    assert fetched.id == template.id
    assert fetched.name == template.name


@pytest.mark.asyncio
async def test_get_templates(
    db: Session,
    context_template_data: dict[str, str],
    another_context_template_data: dict[str, str],
) -> None:
    """Test retrieving multiple ContextTemplates."""
    await crud.context_template.create(
        db, obj_in=models.ContextTemplateCreate(**context_template_data)
    )
    await crud.context_template.create(
        db, obj_in=models.ContextTemplateCreate(**another_context_template_data)
    )
    templates = await crud.context_template.get_all(db)
    assert len(templates) >= 2
    names = [t.name for t in templates]
    assert context_template_data["name"] in names
    assert another_context_template_data["name"] in names


@pytest.mark.asyncio
async def test_update_context_template(db: Session, context_template_data: dict[str, str]) -> None:
    """Test updating a ContextTemplate."""
    obj_in = models.ContextTemplateCreate(**context_template_data)
    template = await crud.context_template.create(db, obj_in=obj_in)
    update_in = models.ContextTemplateUpdate(name="Updated Name", description="Updated desc.")
    updated = await crud.context_template.update(db, id=template.id, obj_in=update_in)
    assert updated.name == "Updated Name"
    assert updated.description == "Updated desc."
    assert updated.updated_at >= template.updated_at


@pytest.mark.asyncio
async def test_delete_context_template(db: Session, context_template_data: dict[str, str]) -> None:
    """Test deleting a ContextTemplate."""
    obj_in = models.ContextTemplateCreate(**context_template_data)
    template = await crud.context_template.create(db, obj_in=obj_in)
    await crud.context_template.remove(db, id=template.id)
    with pytest.raises(RecordNotFoundError):
        await crud.context_template.get(db, id=template.id)


@pytest.mark.asyncio
async def test_add_and_remove_section_to_context_template(
    db: Session, context_template_data: dict[str, str]
) -> None:
    """Test adding and removing a section to/from a context template."""
    # Create template
    obj_in = models.ContextTemplateCreate(**context_template_data)
    template = await crud.context_template.create(db, obj_in=obj_in)
    # Create section
    section_in = models.ContextSectionCreate(name="Section 1", description="Section for testing")
    section = await crud.context_section.create(db, obj_in=section_in)
    # Add section to template
    updated = await crud.context_template.add_section(
        db, context_template_id=template.id, section_id=section.id
    )
    assert any(s.id == section.id for s in updated.sections)
    # Remove section from template
    updated = await crud.context_template.remove_section(
        db, context_template_id=template.id, section_id=section.id
    )
    assert all(s.id != section.id for s in updated.sections)


@pytest.mark.asyncio
def make_section(db: Session, name: str) -> models.ContextSection:
    section_in = models.ContextSectionCreate(name=name, description=f"Section {name}")
    return db.run_sync(lambda: crud.context_section.create(db, obj_in=section_in))


@pytest.mark.asyncio
async def test_reorder_sections_in_context_template(
    db: Session, context_template_data: dict[str, str]
) -> None:
    """Test reordering sections in a context template."""
    # Create template
    obj_in = models.ContextTemplateCreate(**context_template_data)
    template = await crud.context_template.create(db, obj_in=obj_in)
    # Create and add sections
    section_names = ["A", "B", "C"]
    sections = [
        await crud.context_section.create(
            db, obj_in=models.ContextSectionCreate(name=n, description=f"Section {n}")
        )
        for n in section_names
    ]
    for section in sections:
        await crud.context_template.add_section(
            db, context_template_id=template.id, section_id=section.id
        )
    # Reorder: C, A, B
    new_order = [sections[2].id, sections[0].id, sections[1].id]
    updated = await crud.context_template.reorder_sections(
        db, context_template_id=template.id, section_ids=new_order
    )
    ordered_ids = [s.id for s in updated.sections]
    assert ordered_ids == new_order
