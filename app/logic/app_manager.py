import subprocess

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
            command = f"bash -c 'echo > /dev/tcp/172.27.0.1/{self.port_connect}'"
            subprocess.run(command, shell=True, check=True, capture_output=True)
            print(f"Application {self.name} is running on port {self.port_connect}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"Application {self.name} is not running on port {self.port_connect}")
            return False

    def kill(self) -> None:
        """Kills the application."""
        command = (
            f"fuser -k {self.port_connect}/tcp" if not self.command_stop else self.command_stop
        )

        # Run kill command
        if not command:
            raise ValueError("command is not set.")

        try:
            subprocess.run(command, shell=True, check=True, capture_output=True)
        except subprocess.CalledProcessError:
            raise ValueError("Failed to kill the application. Command: {command}")

        # Check if the application is killed
        if self.is_running:
            raise ValueError("Failed to kill the application. Needs debug.")
