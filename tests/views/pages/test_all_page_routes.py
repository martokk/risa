import pytest
from fastapi.testclient import TestClient
from httpx import Cookies


@pytest.mark.asyncio
async def test_all_page_routes(client: TestClient, normal_user_cookies: Cookies) -> None:
    """Test that all page routes load successfully."""
    # Set cookies for authentication
    client.cookies = normal_user_cookies

    # Create a context template to ensure the detail route exists
    template_data = {
        "name": "Test Template for Route",
        "description": "Test template created for route testing.",
    }
    create_resp = client.post("/api/v1/context-templates/", json=template_data)
    assert create_resp.status_code == 201, f"Failed to create context template: {create_resp.text}"
    template_id = create_resp.json()["id"]

    # Define all routes to test with their expected status codes
    routes = [
        # Public routes (no auth required)
        ("/login", 200),
        ("/favicon.ico", 200),
        # Protected routes (auth required)
        ("/", 200),
        ("/dashboard", 200),
        ("/organizations", 200),
        ("/organizations/new", 200),
        ("/grant-programs", 200),
        ("/grant-cycles", 200),
        ("/grant-proposals", 200),
        ("/calendar/upcoming", 200),
        ("/spreadsheet", 200),
        ("/tools/calculators", 200),
        ("/context-templates/", 200),
        (f"/context-templates/{template_id}/", 200),  # Use created template's ID
    ]

    # Test each route
    for route, expected_status in routes:
        if route in ["/login", "/favicon.ico"]:
            # Public routes don't need auth
            response = client.get(route)
        else:
            # Protected routes use cookies for auth
            response = client.get(route)

        assert (
            response.status_code == expected_status
        ), f"Route {route} failed with status {response.status_code}"
