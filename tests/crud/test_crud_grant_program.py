import pytest
from sqlmodel import Session

from app import crud, models


@pytest.fixture
def grant_program_data() -> dict[str, str]:
    return {
        "name": "Test Grant Program",
        "organization_id": "1",
        "description": "Test Description",
        "url": "https://test.com",
        "status": "Active",
        "frequency": "Monthly",
    }


@pytest.fixture
def context_data() -> dict[str, int | None]:
    return {"template_id": 1, "name": "GP Context"}


@pytest.mark.asyncio
async def test_create_context_for_grant_program(
    db: Session, grant_program_data: dict[str, str], context_data: dict[str, int | None]
) -> None:
    """Test creating a Context linked to a Grant Program."""
    gp = await crud.grant_program.create(db, obj_in=models.GrantProgramCreate(**grant_program_data))
    context = await crud.grant_program.create_context(
        db, grant_program_id=gp.id, context_in=models.ContextCreate(**context_data)
    )
    assert context.id is not None
    assert context.grant_program.id == gp.id
    assert context.name == context_data["name"]
