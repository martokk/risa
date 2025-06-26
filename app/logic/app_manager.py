import subprocess
from typing import Any

from pydantic import BaseModel, Field

from app import logger


class AppManagerApp(BaseModel):
    id: str = Field()
    name: str = Field()
    command_start: str | None = Field(default=None)
    command_stop: str | None = Field(default=None)
    command_check_running: str | None = Field(default=None)
    port_connect: int | None = Field(default=None)
    port_internal: int | None = Field(default=None)
    icon_path: str | None = Field(default=None)
    log_file: str | None = Field(default=None)

    @property
    def is_running(self) -> bool:
        """Check if the application is running on the port."""
        if not self.port_connect:
            logger.warning(f"'port_connect' is not set for '{self.name}' app. Check config.")
            return False

        try:
            if self.command_check_running:
                try:
                    subprocess.run(
                        self.command_check_running, shell=True, check=True, capture_output=True
                    )
                except subprocess.CalledProcessError:
                    return False
                return True
            else:
                return False

            # import requests

            # response = requests.get(
            #     f"http://127.0.0.1:{self.port_connect}/", timeout=2, allow_redirects=True
            # )
            # # Check for A1111 specific content
            # return self.name.lower() in response.text.lower()
        except Exception as e:
            logger.error(f"Error checking app content: {e}")
            return False

    def start(self) -> dict[str, Any]:
        """Starts the application."""
        if not self.command_start:
            raise ValueError(f"command_start is not set for `{self.id}`")

        try:
            subprocess.run(self.command_start, shell=True, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise ValueError(
                f"Failed to start the application. <br><br>Command: {self.command_start} <br><br>stderr: <strong>{e.stderr}</strong>"
            ) from e

        return {
            "success": True,
            "message": f"Called command_start for `{self.id}`",
        }

    def kill(self) -> dict[str, Any]:
        """Kills the application."""

        if not self.command_stop:
            raise ValueError(f"command_stop is not set for `{self.id}`")

        try:
            subprocess.run(self.command_stop, shell=True, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise ValueError("Failed to stop the application. Command: {self.command_stop}") from e

        # Check if the application is killed
        if self.is_running:
            raise ValueError("Failed to kill the application. Needs debug.")

        return {
            "success": True,
            "message": f"Killed {self.name} at {self.port_internal}:{self.port_connect}",
        }

    def stop(self) -> dict[str, bool]:
        return self.kill()
