from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio

TEXT_URL = "/api/v1/context-sections-texts/"
SECTION_URL = "/api/v1/context-sections/"
CONTEXT_URL = "/api/v1/contexts/"


@pytest.fixture
async def context_id(async_client: AsyncClient) -> int:
    resp = await async_client.post(CONTEXT_URL, json={"name": "Test Context", "template_id": None})
    return resp.json()["id"]


@pytest.fixture
async def section_id(async_client: AsyncClient) -> int:
    unique_name = f"Section {uuid4()}"
    resp = await async_client.post(SECTION_URL, json={"name": unique_name, "description": "desc"})
    return resp.json()["id"]


@pytest.fixture
def text_data(context_id: int, section_id: int) -> dict[str, int | str]:
    return {"context_id": context_id, "section_id": section_id, "text": "Initial text."}


async def test_create_context_section_text(
    async_client: AsyncClient, text_data: dict[str, int | str]
) -> None:
    """Test creating a ContextSectionText."""
    response = await async_client.post(TEXT_URL, json=text_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["context_id"] == text_data["context_id"]
    assert data["section_id"] == text_data["section_id"]
    assert data["text"] == text_data["text"]
    assert "id" in data


async def test_list_context_section_texts(
    async_client: AsyncClient, text_data: dict[str, int | str]
) -> None:
    """Test listing all ContextSectionTexts."""
    await async_client.post(TEXT_URL, json=text_data)
    await async_client.post(TEXT_URL, json=text_data)
    response = await async_client.get(TEXT_URL)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


async def test_get_context_section_text(
    async_client: AsyncClient, text_data: dict[str, int | str]
) -> None:
    """Test retrieving a ContextSectionText by ID."""
    create_resp = await async_client.post(TEXT_URL, json=text_data)
    text_id = create_resp.json()["id"]
    response = await async_client.get(f"{TEXT_URL}{text_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == text_id
    assert data["text"] == text_data["text"]


async def test_update_context_section_text(
    async_client: AsyncClient, text_data: dict[str, int | str]
) -> None:
    """Test updating a ContextSectionText."""
    create_resp = await async_client.post(TEXT_URL, json=text_data)
    text_id = create_resp.json()["id"]
    update_data = {"text": "Updated text."}
    response = await async_client.put(f"{TEXT_URL}{text_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["text"] == "Updated text."


async def test_delete_context_section_text(
    async_client: AsyncClient, text_data: dict[str, int | str]
) -> None:
    """Test deleting a ContextSectionText."""
    create_resp = await async_client.post(TEXT_URL, json=text_data)
    text_id = create_resp.json()["id"]
    response = await async_client.delete(f"{TEXT_URL}{text_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    # Confirm deletion
    get_resp = await async_client.get(f"{TEXT_URL}{text_id}")
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND


async def test_get_context_section_text_not_found(async_client: AsyncClient) -> None:
    """Test getting a non-existent ContextSectionText."""
    response = await async_client.get(f"{TEXT_URL}999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_update_context_section_text_not_found(async_client: AsyncClient) -> None:
    """Test updating a non-existent ContextSectionText."""
    update_data = {"text": "Doesn't Matter"}
    response = await async_client.put(f"{TEXT_URL}999999", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_context_section_text_not_found(async_client: AsyncClient) -> None:
    """Test deleting a non-existent ContextSectionText."""
    response = await async_client.delete(f"{TEXT_URL}999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_create_context_section_text_invalid(async_client: AsyncClient) -> None:
    """Test creating a ContextSectionText with invalid data (missing required fields)."""
    # Missing required fields
    response = await async_client.post(TEXT_URL, json={"text": "desc only"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
