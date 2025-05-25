from typing import Any
from unittest.mock import MagicMock, patch

import uvicorn

from app import settings
from app.core.server import start_server


def test_start_server_host_port(monkeypatch: MagicMock) -> None:
    def mock_run(*args: Any, **kwargs: Any) -> None:
        assert kwargs["host"] == settings.SERVER_HOST
        assert kwargs["port"] == settings.SERVER_PORT

    monkeypatch.setattr(uvicorn, "run", mock_run)
    start_server()


def test_start_server_log_level(monkeypatch: MagicMock) -> None:
    def mock_run(*args: Any, **kwargs: Any) -> None:
        assert kwargs["log_level"] == settings.LOG_LEVEL.lower()

    monkeypatch.setattr(uvicorn, "run", mock_run)
    start_server()


def test_start_server() -> None:
    """Tests that the start_server function calls uvicorn.run with the correct arguments."""
    with patch("uvicorn.run") as mock_run:
        start_server()
        mock_run.assert_called_once()
        assert mock_run.call_args[1]["host"] == settings.SERVER_HOST
        assert mock_run.call_args[1]["port"] == settings.SERVER_PORT
        assert mock_run.call_args[1]["log_level"] == settings.LOG_LEVEL.lower()
        assert mock_run.call_args[1]["reload"] == settings.UVICORN_RELOAD
        assert mock_run.call_args[1]["app_dir"] == ""
