import pytest
from fastapi import status
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio

CONTEXT_URL = "/api/v1/contexts/"
ORG_URL = "/api/v1/organizations/"
GRANT_PROGRAM_URL = "/api/v1/grant-programs/"


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
def grant_program_data() -> dict[str, str]:
    return {"name": "Test Grant Program"}


@pytest.fixture
def context_data() -> dict[str, int | None]:
    # template_id is optional, use a random int for uniqueness
    return {"template_id": None, "name": "Test Context"}


async def test_create_context(
    async_client: AsyncClient, context_data: dict[str, int | None]
) -> None:
    """Test creating a Context."""
    response = await async_client.post(CONTEXT_URL, json=context_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["template_id"] == context_data["template_id"]


async def test_list_contexts(
    async_client: AsyncClient, context_data: dict[str, int | None]
) -> None:
    """Test listing all Contexts."""
    await async_client.post(CONTEXT_URL, json=context_data)
    await async_client.post(CONTEXT_URL, json=context_data)
    response = await async_client.get(CONTEXT_URL)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


async def test_get_context(async_client: AsyncClient, context_data: dict[str, int | None]) -> None:
    """Test retrieving a Context by ID."""
    create_resp = await async_client.post(CONTEXT_URL, json=context_data)
    context_id = create_resp.json()["id"]
    response = await async_client.get(f"{CONTEXT_URL}{context_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == context_id
    assert data["template_id"] == context_data["template_id"]


async def test_update_context(
    async_client: AsyncClient, context_data: dict[str, int | None]
) -> None:
    """Test updating a Context."""
    create_resp = await async_client.post(CONTEXT_URL, json=context_data)
    context_id = create_resp.json()["id"]
    update_data = {"template_id": 12345}
    response = await async_client.put(f"{CONTEXT_URL}{context_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["template_id"] == 12345


async def test_delete_context(
    async_client: AsyncClient, context_data: dict[str, int | None]
) -> None:
    """Test deleting a Context."""
    create_resp = await async_client.post(CONTEXT_URL, json=context_data)
    context_id = create_resp.json()["id"]
    response = await async_client.delete(f"{CONTEXT_URL}{context_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    # Confirm deletion
    get_resp = await async_client.get(f"{CONTEXT_URL}{context_id}")
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND


async def test_get_context_not_found(async_client: AsyncClient) -> None:
    """Test getting a non-existent Context."""
    response = await async_client.get(f"{CONTEXT_URL}999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_update_context_not_found(async_client: AsyncClient) -> None:
    """Test updating a non-existent Context."""
    update_data = {"template_id": 54321}
    response = await async_client.put(f"{CONTEXT_URL}999999", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_context_not_found(async_client: AsyncClient) -> None:
    """Test deleting a non-existent Context."""
    response = await async_client.delete(f"{CONTEXT_URL}999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_create_context_invalid(async_client: AsyncClient) -> None:
    """Test creating a Context with invalid data (missing required fields)."""
    response = await async_client.post(CONTEXT_URL, json={})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
