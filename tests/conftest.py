from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from fastapi import Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.testclient import TestClient
from httpx import AsyncClient, Cookies
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, create_engine
from starlette.datastructures import URL

from app import crud, models, settings
from app.core import security
from app.core.app import app
from app.core.db import get_db, initialize_tables_and_initial_data


# Set up the database
db_url = "sqlite:///:memory:"
engine = create_engine(
    db_url,
    echo=False,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)
SQLModel.metadata.drop_all(bind=engine)
SQLModel.metadata.create_all(bind=engine)


# These two event listeners are only needed for sqlite for proper
# SAVEPOINT / nested transaction support. Other databases like postgres
# don't need them.
# From: https://docs.sqlalchemy.org/en/14/dialects/sqlite.html
# #serializable-isolation-savepoints-transactional-ddl
@sa.event.listens_for(engine, "connect")  # type: ignore
def do_connect(dbapi_connection: Any, connection_record: Any) -> None:
    # disable pysqlite's emitting of the BEGIN statement entirely.
    # also stops it from emitting COMMIT before any DDL.
    dbapi_connection.isolation_level = None


@sa.event.listens_for(engine, "begin")  # type: ignore
def do_begin(conn: Any) -> None:
    # emit our own BEGIN
    conn.exec_driver_sql("BEGIN")


@pytest.fixture(name="init")
def fixture_init(mocker: MagicMock, tmp_path: Path) -> None:  # pylint: disable=unused-argument
    # mocker.patch("app.paths.FEEDS_PATH", return_value=tmp_path)
    pass


@pytest.fixture(name="db")
async def fixture_db(init: Any) -> AsyncGenerator[Session, None]:  # pylint: disable=unused-argument
    connection = engine.connect()
    transaction = connection.begin()
    db = TestingSessionLocal(bind=connection)

    # Begin a nested transaction (using SAVEPOINT).
    nested = connection.begin_nested()
    await initialize_tables_and_initial_data(db=db)

    # If the application code calls session.commit, it will end the nested
    # transaction. Need to start a new one when that happens.
    @sa.event.listens_for(db, "after_transaction_end")  # type: ignore
    def end_savepoint(  # type: ignore
        db: Any,
        transaction: Any,  # pylint: disable=unused-argument
    ) -> None:
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield db

    # Rollback the overall transaction, restoring the state before the test ran.
    db.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(name="client")
async def fixture_client(db: Session) -> AsyncGenerator[TestClient, None]:
    """
    Fixture that creates a test client with the database session override.

    Args:
        db (Session): database session.

    Yields:
        TestClient: test client with database session override.
    """

    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(name="db_with_user")
async def fixture_db_with_user(db: Session) -> Session:
    """
    Fixture that creates an example user in the test database.

    Args:
        db (Session): database session.

    Returns:
        Session: database session with example user.
    """
    # user_hashed_password = security.get_password_hash("test_password")
    user_create = models.UserCreateWithPassword(
        username="test_user", email="test@example.com", password="test_password"
    )
    await crud.user._create_with_password(obj_in=user_create, db=db)

    return db


@pytest.fixture(name="superuser_token_headers")
def superuser_token_headers(db_with_user: Session, client: TestClient) -> dict[str, str]:
    """
    Fixture that returns the headers for a superuser.

    Args:
        db_with_user (Session): database session.
        client (TestClient): test client.

    Returns:
        dict[str, str]: headers for a superuser.
    """
    login_data = {
        "username": settings.FIRST_SUPERUSER_USERNAME,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.post(f"{settings.API_V1_PREFIX}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    return {"Authorization": f"Bearer {a_token}"}


@pytest.fixture(name="normal_user_token_headers")
def normal_user_token_headers(client: TestClient) -> dict[str, str]:
    """
    Fixture that returns the headers for a normal user.

    Args:
        client (TestClient): test client.

    Returns:
        dict[str, str]: headers for a normal user.
    """
    login_data = {
        "username": "test_user",
        "password": "test_password",
    }
    r = client.post(f"{settings.API_V1_PREFIX}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    return {"Authorization": f"Bearer {a_token}"}


@pytest.fixture(name="test_request")
def fixture_request() -> Request:
    """
    Fixture that returns a request object.

    Returns:
        Request: request object.
    """
    return Request(scope={"type": "http", "method": "GET", "path": "/"})


@pytest.fixture(name="normal_user_cookies")
async def fixture_normal_user_cookies(
    db_with_user: Session,
    client: TestClient,  # pylint: disable=unused-argument
) -> Cookies:
    """
    Fixture that returns the cookie_data for a normal user.

    Args:
        db_with_user (Session): database session.
        client (TestClient): test client.

    Returns:
        Cookies: cookie_data for a normal user.
    """
    form_data = OAuth2PasswordRequestForm(username="test_user", password="test_password", scope="")
    tokens = await security.get_tokens_from_username_password(db=db_with_user, form_data=form_data)
    cookies = Cookies()
    cookies.set("access_token", f"Bearer {tokens.access_token}")
    cookies.set("refresh_token", f"Bearer {tokens.refresh_token}")
    return cookies


@pytest.fixture(name="superuser_cookies")
async def fixture_superuser_cookies(
    db_with_user: Session,
    client: TestClient,  # pylint: disable=unused-argument
) -> Cookies:
    """
    Fixture that returns the cookie_data for a superuser.

    Args:
        db_with_user (Session): database session.
        client (TestClient): test client.

    Returns:
        Cookies: cookie_data for a superuser.
    """
    form_data = OAuth2PasswordRequestForm(
        username=settings.FIRST_SUPERUSER_USERNAME,
        password=settings.FIRST_SUPERUSER_PASSWORD,
        scope="",
    )
    tokens = await security.get_tokens_from_username_password(db=db_with_user, form_data=form_data)
    cookies = Cookies()
    cookies.set("access_token", f"Bearer {tokens.access_token}")
    cookies.set("refresh_token", f"Bearer {tokens.refresh_token}")
    return cookies


class MockRequest(Request):
    def __init__(self, scope: dict[str, Any]) -> None:
        super().__init__(scope)
        self._state = {}  # type: ignore

    def url_for(self, __name: str, /, **path_params: Any) -> URL:
        """Mock url_for to always return a test URL"""
        return URL(path="/")

    @property
    def url(self) -> URL:
        """Mock url property to return a test URL"""
        server_host, server_port = self.scope.get("server", ("testserver", 80))
        return URL(
            scheme=self.scope.get("scheme", "http"),
            netloc=f"{server_host}:{server_port}",
            path=self.scope.get("path", "/"),
            query=self.scope.get("query_string", b"").decode(),
        )

    @property
    def method(self) -> str:
        """Mock method property"""
        return self.scope.get("method", "GET")

    @property
    def state(self) -> Any:
        """Mock state property"""
        return self._state


@pytest.fixture
async def async_client(db: Session) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client with DB dependency override."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
async def test_user_token(db_with_user: Session) -> str:
    """Create a test user token."""
    form_data = OAuth2PasswordRequestForm(username="test_user", password="test_password", scope="")
    tokens = await security.get_tokens_from_username_password(db=db_with_user, form_data=form_data)
    return f"Bearer {tokens.access_token}"
