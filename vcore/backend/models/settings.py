from zoneinfo import ZoneInfo

from pydantic import EmailStr, validator
from pydantic_settings import BaseSettings


class PythonFastAPIBaseSettings(BaseSettings):
    # Environment Settings #
    ENV_NAME: str = "invalid_default_value"
    DEBUG: bool = True

    # THEME
    ACCENT: str = "#0000ff"

    # Log
    LOG_LEVEL: str = "INFO"

    # Database
    DB_URL: str = "sqlite:///"
    DATABASE_ECHO: bool = False

    # Huey Job Queue
    HUEY_DEFAULT_SQLITE_PATH: str = "data/huey_consumer__default.db"
    HUEY_RESERVED_SQLITE_PATH: str = "data/huey_consumer__reserved.db"

    HUEY_DEFAULT_LOG_PATH: str = "data/logs/huey_consumer__default.log"
    HUEY_RESERVED_LOG_PATH: str = "data/logs/huey_consumer__reserved.log"

    # Server
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 5000
    BASE_DOMAIN: str = "localhost:5000"
    BASE_URL: str = "http://localhost:5000"
    PROXY_HOST: str = "127.0.0.1"
    UVICORN_RELOAD: bool = True
    UVICORN_ENTRYPOINT: str = "app.app:app"
    UVICORN_WORKERS: int = 1

    # API
    API_V1_PREFIX: str = "/api/v1"
    JWT_ACCESS_SECRET_KEY: str = "invalid_default_value"
    JWT_REFRESH_SECRET_KEY: str = "invalid_default_value"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080
    ALGORITHM: str = "HS256"

    # Email
    SMTP_TLS: bool = True
    SMTP_PORT: int | None = None
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: str | None = None

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    EMAILS_ENABLED: bool = False

    # Users
    FIRST_SUPERUSER_USERNAME: str = "invalid_default_value"
    FIRST_SUPERUSER_EMAIL: EmailStr = "invalid@default-value.com"
    FIRST_SUPERUSER_PASSWORD: str = "invalid_default_value"
    USERS_OPEN_REGISTRATION: bool = False

    # Notify
    NOTIFY_EMAIL_ENABLED: bool = False
    NOTIFY_EMAIL_TO: EmailStr | None = None
    NOTIFY_TELEGRAM_ENABLED: bool = False
    TELEGRAM_API_TOKEN: str = ""
    TELEGRAM_CHAT_ID: int = 0
    NOTIFY_ON_START: bool = False

    # Project Settings
    PROJECT_NAME: str = "invalid_default_value"
    PACKAGE_NAME: str = PROJECT_NAME.lower().replace("-", "_").replace(" ", "_")
    PROJECT_DESCRIPTION: str = f"{PROJECT_NAME}"
    VERSION: str | None = None

    # GitHub Webhook
    GITHUB_DEPLOY_WEBHOOK: str = ""
    DOCKER_HOST: str = ""
    NETCAT_PORT: int = 5001

    # Time Settings
    TIMEZONE: str = "America/Chicago"  # Default to CST

    # LLM
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    PHI_API_KEY: str = ""

    @property
    def TIMEZONE_INFO(self) -> ZoneInfo:
        """Get the timezone info object."""
        return ZoneInfo(self.TIMEZONE)

    @validator("ENV_NAME")
    def validate_env_name(cls, v: str) -> str:
        """Validate that ENV_NAME is provided and not the default value."""
        if v == "invalid_default_value":
            raise ValueError("ENV_NAME must be provided via environment variable or .env file")
        return v

    @validator("JWT_ACCESS_SECRET_KEY")
    def validate_jwt_access_secret_key(cls, v: str) -> str:
        """Validate that JWT_ACCESS_SECRET_KEY is provided and not the default value."""
        if v == "invalid_default_value":
            raise ValueError(
                "JWT_ACCESS_SECRET_KEY must be provided via environment variable or .env file"
            )
        return v

    @validator("JWT_REFRESH_SECRET_KEY")
    def validate_jwt_refresh_secret_key(cls, v: str) -> str:
        """Validate that JWT_REFRESH_SECRET_KEY is provided and not the default value."""
        if v == "invalid_default_value":
            raise ValueError(
                "JWT_REFRESH_SECRET_KEY must be provided via environment variable or .env file"
            )
        return v

    @validator("FIRST_SUPERUSER_EMAIL")
    def validate_first_superuser_email(cls, v: EmailStr) -> EmailStr:
        """Validate that FIRST_SUPERUSER_EMAIL is provided and not the default value."""
        if v == "invalid@default-value.com":
            raise ValueError(
                "FIRST_SUPERUSER_EMAIL must be provided via environment variable or .env file"
            )
        return v

    @validator("FIRST_SUPERUSER_PASSWORD")
    def validate_first_superuser_password(cls, v: str) -> str:
        """Validate that FIRST_SUPERUSER_PASSWORD is provided and not the default value."""
        if v == "invalid_default_value":
            raise ValueError(
                "FIRST_SUPERUSER_PASSWORD must be provided via environment variable or .env file"
            )
        return v

    @validator("FIRST_SUPERUSER_USERNAME")
    def validate_first_superuser_username(cls, v: str) -> str:
        """Validate that FIRST_SUPERUSER_USERNAME is provided and not the default value."""
        if v == "invalid_default_value":
            raise ValueError(
                "FIRST_SUPERUSER_USERNAME must be provided via environment variable or .env file"
            )
        return v

    @validator("PROJECT_NAME")
    def validate_project_name(cls, v: str) -> str:
        """Validate that PROJECT_NAME is provided and not the default value."""
        if v == "invalid_default_value":
            raise ValueError("PROJECT_NAME must be provided via environment variable or .env file")
        return v
