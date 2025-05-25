from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio

SECTION_URL = "/api/v1/context-sections/"


@pytest.fixture
def section_data() -> dict[str, str]:
    unique_name = f"Section {uuid4()}"
    return {"name": unique_name, "description": "A test section."}


@pytest.fixture
def another_section_data() -> dict[str, str]:
    unique_name = f"Section {uuid4()}"
    return {"name": unique_name, "description": "Another test section."}


async def test_create_context_section(
    async_client: AsyncClient, section_data: dict[str, str]
) -> None:
    """Test creating a ContextSection."""
    response = await async_client.post(SECTION_URL, json=section_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == section_data["name"]
    assert data["description"] == section_data["description"]
    assert "id" in data


async def test_list_context_sections(
    async_client: AsyncClient, section_data: dict[str, str], another_section_data: dict[str, str]
) -> None:
    """Test listing all ContextSections."""
    await async_client.post(SECTION_URL, json=section_data)
    await async_client.post(SECTION_URL, json=another_section_data)
    response = await async_client.get(SECTION_URL)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    names = [s["name"] for s in data]
    assert section_data["name"] in names
    assert another_section_data["name"] in names


async def test_get_context_section(async_client: AsyncClient, section_data: dict[str, str]) -> None:
    """Test retrieving a ContextSection by ID."""
    create_resp = await async_client.post(SECTION_URL, json=section_data)
    section_id = create_resp.json()["id"]
    response = await async_client.get(f"{SECTION_URL}{section_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == section_id
    assert data["name"] == section_data["name"]


async def test_update_context_section(
    async_client: AsyncClient, section_data: dict[str, str]
) -> None:
    """Test updating a ContextSection."""
    create_resp = await async_client.post(SECTION_URL, json=section_data)
    section_id = create_resp.json()["id"]
    update_data = {"name": f"Updated {uuid4()}", "description": "Updated desc."}
    response = await async_client.put(f"{SECTION_URL}{section_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]


async def test_delete_context_section(
    async_client: AsyncClient, section_data: dict[str, str]
) -> None:
    """Test deleting a ContextSection."""
    create_resp = await async_client.post(SECTION_URL, json=section_data)
    section_id = create_resp.json()["id"]
    response = await async_client.delete(f"{SECTION_URL}{section_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    # Confirm deletion
    get_resp = await async_client.get(f"{SECTION_URL}{section_id}")
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND


async def test_get_context_section_not_found(async_client: AsyncClient) -> None:
    """Test getting a non-existent ContextSection."""
    response = await async_client.get(f"{SECTION_URL}999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_update_context_section_not_found(async_client: AsyncClient) -> None:
    """Test updating a non-existent ContextSection."""
    update_data = {"name": "Doesn't Matter", "description": "Doesn't Matter"}
    response = await async_client.put(f"{SECTION_URL}999999", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_context_section_not_found(async_client: AsyncClient) -> None:
    """Test deleting a non-existent ContextSection."""
    response = await async_client.delete(f"{SECTION_URL}999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_create_context_section_invalid(async_client: AsyncClient) -> None:
    """Test creating a ContextSection with invalid data (missing required fields)."""
    # Missing required 'name'
    response = await async_client.post(SECTION_URL, json={"description": "desc only"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
