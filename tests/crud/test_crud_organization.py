import pytest
from sqlmodel import Session

from app import crud, models


@pytest.fixture
def organization_data() -> dict[str, str]:
    return {
        "name": "Test Organization",
        "description": "Test Description",
        "organization_type": "Non-Profit",
        "status": "Active",
        "url": "https://test.com",
    }


@pytest.fixture
def context_data() -> dict[str, int | None]:
    return {"template_id": 1, "name": "Org Context"}


@pytest.mark.asyncio
async def test_create_context_for_organization(
    db: Session, organization_data: dict[str, str], context_data: dict[str, int | None]
) -> None:
    """Test creating a Context linked to an Organization."""
    org = await crud.organization.create(db, obj_in=models.OrganizationCreate(**organization_data))
    context = await crud.organization.create_context(
        db, organization_id=org.id, context_in=models.ContextCreate(**context_data)
    )
    assert context.id is not None
    assert context.organization.id == org.id
    assert context.name == context_data["name"]
