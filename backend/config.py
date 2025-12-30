from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = Field(default="TaskGenie", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")

    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/taskgenie.db", alias="DATABASE_URL"
    )

    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8080, alias="PORT")

    llm_provider: str = Field(default="openrouter", alias="LLM_PROVIDER")
    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")
    llm_model: str = Field(default="anthropic/claude-3-haiku", alias="LLM_MODEL")

    gmail_enabled: bool = Field(default=False, alias="GMAIL_ENABLED")
    gmail_credentials_path: str | None = Field(default=None, alias="GMAIL_CREDENTIALS_PATH")

    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")
    github_username: str | None = Field(default=None, alias="GITHUB_USERNAME")

    notifications_enabled: bool = Field(default=True, alias="NOTIFICATIONS_ENABLED")
    notification_schedule: list[str] = Field(default=["24h", "6h"], alias="NOTIFICATION_SCHEDULE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
