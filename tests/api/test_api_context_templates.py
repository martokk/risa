from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio

TEMPLATE_URL = "/api/v1/context-templates/"


@pytest.fixture
def template_data():
    unique_name = f"Test Template {uuid4()}"
    return {"name": unique_name, "description": "A template for testing."}


@pytest.fixture
def another_template_data():
    unique_name = f"Another Template {uuid4()}"
    return {"name": unique_name, "description": "Another template for testing."}


async def test_create_context_template(async_client: AsyncClient, template_data):
    response = await async_client.post(TEMPLATE_URL, json=template_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == template_data["name"]
    assert data["description"] == template_data["description"]
    assert "id" in data


async def test_list_context_templates(
    async_client: AsyncClient, template_data, another_template_data
):
    # Create two templates
    await async_client.post(TEMPLATE_URL, json=template_data)
    await async_client.post(TEMPLATE_URL, json=another_template_data)
    response = await async_client.get(TEMPLATE_URL)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    names = [t["name"] for t in data]
    assert template_data["name"] in names
    assert another_template_data["name"] in names


async def test_get_context_template(async_client: AsyncClient, template_data):
    create_resp = await async_client.post(TEMPLATE_URL, json=template_data)
    template_id = create_resp.json()["id"]
    response = await async_client.get(f"{TEMPLATE_URL}{template_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == template_id
    assert data["name"] == template_data["name"]


async def test_update_context_template(async_client: AsyncClient, template_data):
    create_resp = await async_client.post(TEMPLATE_URL, json=template_data)
    template_id = create_resp.json()["id"]
    update_data = {"name": f"Updated Name {uuid4()}", "description": "Updated desc."}
    response = await async_client.put(f"{TEMPLATE_URL}{template_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]


async def test_delete_context_template(async_client: AsyncClient, template_data):
    create_resp = await async_client.post(TEMPLATE_URL, json=template_data)
    template_id = create_resp.json()["id"]
    response = await async_client.delete(f"{TEMPLATE_URL}{template_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    # Confirm deletion
    get_resp = await async_client.get(f"{TEMPLATE_URL}{template_id}")
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND


async def test_get_context_template_not_found(async_client: AsyncClient):
    response = await async_client.get(f"{TEMPLATE_URL}999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_update_context_template_not_found(async_client: AsyncClient):
    update_data = {"name": f"Doesn't Matter {uuid4()}", "description": "Doesn't Matter"}
    response = await async_client.put(f"{TEMPLATE_URL}999999", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_context_template_not_found(async_client: AsyncClient):
    response = await async_client.delete(f"{TEMPLATE_URL}999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_create_context_template_invalid(async_client: AsyncClient):
    # Missing required 'name'
    response = await async_client.post(TEMPLATE_URL, json={"description": "desc only"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_add_and_remove_section_to_context_template(async_client: AsyncClient, template_data):
    # Create template
    create_resp = await async_client.post(TEMPLATE_URL, json=template_data)
    assert create_resp.status_code == status.HTTP_201_CREATED
    template_id = create_resp.json()["id"]
    # Create section
    section_data = {"name": f"Section {uuid4()}", "description": "Section for testing"}
    section_resp = await async_client.post("/api/v1/context-sections/", json=section_data)
    assert section_resp.status_code == status.HTTP_201_CREATED
    section_id = section_resp.json()["id"]
    # Add section to template
    add_resp = await async_client.post(
        f"{TEMPLATE_URL}{template_id}/sections/", json={"section_id": section_id}
    )
    assert add_resp.status_code == status.HTTP_200_OK
    data = add_resp.json()
    assert any(s["id"] == section_id for s in data["sections"])
    # Remove section from template
    remove_resp = await async_client.delete(f"{TEMPLATE_URL}{template_id}/sections/{section_id}/")
    assert remove_resp.status_code == status.HTTP_200_OK
    data = remove_resp.json()
    assert all(s["id"] != section_id for s in data["sections"])


async def test_reorder_sections_in_context_template(async_client: AsyncClient, template_data):
    # Create template
    create_resp = await async_client.post(TEMPLATE_URL, json=template_data)
    assert create_resp.status_code == status.HTTP_201_CREATED
    template_id = create_resp.json()["id"]
    # Create and add sections
    section_names = ["A", "B", "C"]
    section_ids = []
    for name in section_names:
        section_data = {"name": name, "description": f"Section {name}"}
        section_resp = await async_client.post("/api/v1/context-sections/", json=section_data)
        assert section_resp.status_code == status.HTTP_201_CREATED
        section_id = section_resp.json()["id"]
        section_ids.append(section_id)
        add_resp = await async_client.post(
            f"{TEMPLATE_URL}{template_id}/sections/", json={"section_id": section_id}
        )
        assert add_resp.status_code == status.HTTP_200_OK
    # Reorder: C, A, B
    new_order = [section_ids[2], section_ids[0], section_ids[1]]
    reorder_resp = await async_client.post(
        f"{TEMPLATE_URL}{template_id}/sections/reorder/", json={"section_ids": new_order}
    )
    assert reorder_resp.status_code == status.HTTP_200_OK
    data = reorder_resp.json()
    ordered_ids = [s["id"] for s in data["sections"]]
    assert ordered_ids == new_order
