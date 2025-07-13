from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from vcore.backend import models
from vcore.backend.core import security
from vcore.backend.core.db import get_db
from vcore.backend.templating import templates
from vcore.backend.templating.deps import get_current_tokens


router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    tokens: models.Tokens | None = Depends(get_current_tokens),
    db: Session = Depends(get_db),
) -> Response:
    """
    Login Page.

    Args:
        request(Request): The request object
        tokens(models.Tokens | None): The refreshed tokens

    Returns:
        Response: Login page

    """

    # If tokens are valid, set new tokens as cookies and redirect response
    if tokens:
        # Extract the original URL from the query parameters
        original_url = request.query_params.get("original_url") or "/"
        # Set the cookie
        response = RedirectResponse(original_url, status_code=status.HTTP_302_FOUND)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {tokens.access_token}",
        )
        response.set_cookie(
            key="refresh_token",
            value=f"Bearer {tokens.refresh_token}",
        )
        return response

    # No valid tokens, return login page
    tokens = models.Tokens(access_token="", refresh_token="")
    alerts = models.Alerts().from_cookies(request.cookies)
    return templates.TemplateResponse(
        "login/login.html", {"request": request, "alerts": alerts, "tokens": tokens}
    )


@router.post("/login", response_class=HTMLResponse)
async def handle_login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Response:
    """
    Handle login.

    Args:
        request(Request): The request object
        form_data(OAuth2PasswordRequestForm): The form data (username and password)
        db(Session): The database session.

    Returns:
        Response: Redirect to admin page after login
    """
    try:
        tokens = await security.get_tokens_from_username_password(db=db, form_data=form_data)
    except HTTPException as e:
        return templates.TemplateResponse("login/login.html", {"request": request, "error": e})

    # Set the cookie and redirect to admin
    response = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {tokens.access_token}",
        httponly=True,
        secure=False,
        samesite="lax",
    )
    response.set_cookie(
        key="refresh_token",
        value=f"Bearer {tokens.refresh_token}",
        httponly=True,
        secure=False,
        samesite="lax",
    )

    return response


@router.get("/logout", response_class=HTMLResponse)
async def logout() -> Response:
    """
    Logout user by deleting the cookie.

    Returns:
        Response: Redirect to home page after logout
    """
    alerts = models.Alerts()
    alerts.success.append("You have been logged out.")

    response = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    response.set_cookie(
        key="alerts",
        value=alerts.model_dump_json(),
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=5,
    )
    return response


# @router.get("/register", response_class=HTMLResponse)
# async def register(
#     request: Request,
# ) -> Response:
#     """
#     Args:
#         request(Request): The request object

#     Returns:
#         Response: Registration page
#     """
#     alerts = models.Alerts().from_cookies(request.cookies)
#     return templates.TemplateResponse(
#         "login/register.html",
#         {
#             "request": request,
#             "registration_enabled": settings.USERS_OPEN_REGISTRATION,
#             "alerts": alerts,
#         },
#     )


# @router.post("/register", response_class=HTMLResponse)
# async def handle_registration(
#     request: Request,
#     username: str = Form(None),
#     password: str = Form(None),
#     password_confirmation: str = Form(None),
#     email: str = Form(None),
#     full_name: str = Form(None),
# ) -> Response:
#     """
#     Handle registration.
#     # TODO: Add captcha

#     Args:
#         request(Request): The request object
#         username(str): The username
#         password(str): The password
#         password_confirmation(str): The password confirmation
#         email(str): The email
#         full_name(str): The full name

#     Returns:
#         Response: Registration page
#     """
#     alerts = models.Alerts()
#     if not settings.USERS_OPEN_REGISTRATION:
#         alerts.danger.append("Registration is closed")

#     # Check if all fields are filled
#     if not all([username, password, password_confirmation, email, full_name]):
#         alerts.danger.append("Please fill out all fields")

#     # Confirm passwords match
#     if password != password_confirmation:
#         alerts.danger.append("Passwords do not match")

#     # Validate email via pydantic
#     valid_email = None
#     try:
#         valid_email = EmailStr.validate(email)
#     except (ValueError, TypeError):
#         alerts.danger.append("Invalid email")

#     # Post to the API if there are no errors
#     if not alerts.danger:
#         endpoint = f"{settings.BASE_URL}{settings.API_V1_PREFIX}/register"
#         data = {
#             "username": username,
#             "password": password,
#             "email": valid_email,
#             "full_name": full_name,
#         }
#         async with httpx.AsyncClient() as client:
#             response = await client.post(url=endpoint, json=data, timeout=10)

#         # Handle response
#         if response.status_code == status.HTTP_201_CREATED:
#             alerts.success.append("Registration successful")
#             redirect_response = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
#             redirect_response.set_cookie(
#                 key="alerts", value=alerts.json(), httponly=True, secure=False, samesite="lax",
#                 max_age=5
#             )
#             return redirect_response
#         elif response.status_code == status.HTTP_409_CONFLICT:
#             alerts.danger.append("Username or email already exists")
#         elif response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
#             alerts.danger.append("Invalid data")
#             logger.error(f"Error registering user: {response.status_code=}, {response.text=}")
#         else:
#             logger.error(f"Error registering user: {response.status_code=}, {response.text=}")
#             alerts.danger.append("Error registering user")

#     # Return the registration page with alert messages
#     return templates.TemplateResponse(
#         "login/register.html",
#         {
#             "request": request,
#             "registration_enabled": settings.USERS_OPEN_REGISTRATION,
#             "alerts": alerts,
#         },
#     )
