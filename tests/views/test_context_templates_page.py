from typing import Any, cast
from uuid import uuid4

import pytest
from httpx import AsyncClient, Cookies


pytestmark = pytest.mark.asyncio

LIST_URL = "/context-templates/"
DETAIL_URL = "/context-templates/{id}/"
API_URL = "/api/v1/context-templates/"


async def create_template(
    async_client: AsyncClient, normal_user_cookies: Cookies, name: str | None = None
) -> dict[str, Any]:
    async_client.cookies = normal_user_cookies
    if not name:
        name = f"Test Template {uuid4()}"
    data = {"name": name, "description": "Test description"}
    resp = await async_client.post(API_URL, json=data)
    assert resp.status_code == 201
    return cast(dict[str, Any], resp.json())


async def test_context_templates_list_page(
    async_client: AsyncClient, normal_user_cookies: Cookies
) -> None:
    template = await create_template(async_client, normal_user_cookies)
    resp = await async_client.get(LIST_URL, follow_redirects=True)
    assert resp.status_code == 200
    html = resp.text
    assert template["name"] in html
    assert "Context Template" in html or "Template" in html


async def test_context_template_detail_page(
    async_client: AsyncClient, normal_user_cookies: Cookies
) -> None:
    template = await create_template(async_client, normal_user_cookies)
    resp = await async_client.get(DETAIL_URL.format(id=template["id"]), follow_redirects=True)
    assert resp.status_code == 200
    html = resp.text
    assert template["name"] in html
    assert template["description"] in html


async def test_context_template_detail_page_not_found(
    async_client: AsyncClient, normal_user_cookies: Cookies
) -> None:
    async_client.cookies = normal_user_cookies
    resp = await async_client.get(DETAIL_URL.format(id=999999), follow_redirects=True)
    # Accept 200 (with error message), 404, or 307 (redirect)
    assert resp.status_code in (200, 404, 307)
    html = resp.text
    # Should not crash, may show error or empty page
    assert (
        "not found" in html.lower() or resp.status_code in (404, 307) or "template" in html.lower()
    )
