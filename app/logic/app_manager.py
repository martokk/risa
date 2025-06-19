import subprocess
from typing import Any

from pydantic import BaseModel, Field

from app import logger


class AppManagerApp(BaseModel):
    name: str = Field()
    command_start: str | None = Field(default=None)
    command_stop: str | None = Field(default=None)
    command_health_check: str | None = Field(default=None)
    port_connect: int | None = Field(default=None)
    port_internal: int | None = Field(default=None)
    icon_path: str | None = Field(default=None)

    @property
    def is_running(self) -> bool:
        """Check if the application is running on the port."""
        if not self.port_connect:
            logger.warning(f"'port_connect' is not set for '{self.name}' app. Check config.")
            return False

        try:
            import requests

            response = requests.get(
                f"http://127.0.0.1:{self.port_connect}/", timeout=2, allow_redirects=True
            )
            # Check for A1111 specific content
            return self.name.lower() in response.text.lower()
        except Exception as e:
            logger.error(f"Error checking app content: {e}")
            return False

    def start(self) -> dict[str, Any]:
        """Starts the application."""
        if not self.command_start:
            raise ValueError("command is not set.")

        try:
            subprocess.run(self.command_start, shell=True, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise ValueError(
                "Failed to start the application. Command: {self.command_start}"
            ) from e

        return {
            "success": True,
            "message": f"Started {self.name} at {self.port_connect}",
        }

    def kill(self) -> dict[str, Any]:
        """Kills the application."""
        command = (
            f"fuser -k {self.port_internal}/tcp" if not self.command_stop else self.command_stop
        )

        # Run kill command
        if not command:
            raise ValueError("command is not set.")

        try:
            subprocess.run(command, shell=True, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to kill the application. Command: {command}") from e

        # Check if the application is killed
        if self.is_running:
            raise ValueError("Failed to kill the application. Needs debug.")

        return {
            "success": True,
            "message": f"Killed {self.name} at {self.port_internal}",
        }

    def stop(self) -> dict[str, bool]:
        return self.kill()
