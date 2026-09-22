from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, StringConstraints

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    judge_confidence_threshold: float = Field(default=0.75, ge=0, le=1, allow_inf_nan=False)

    # Tencent Cloud DB placeholders - see backend/.env.example
    tencent_db_host: str = "REPLACE_WITH_TENCENT_DB_HOST"
    tencent_db_port: int = 5432
    tencent_db_user: str = "REPLACE_ME"
    tencent_db_password: str = "REPLACE_ME"
    tencent_db_name: str = "ryde_disputes"
    tencent_db_ssl: str = "require"

    llm_provider: Literal["mock", "tokenhub"] = "mock"
    llm_api_key: str = ""
    llm_base_url: str = "https://tokenhub-intl.tencentcloudmaas.com/v1"
    llm_model: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = "hy3"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.tencent_db_user}:{self.tencent_db_password}"
            f"@{self.tencent_db_host}:{self.tencent_db_port}/{self.tencent_db_name}"
        )

    @property
    def using_placeholder_db(self) -> bool:
        return self.tencent_db_host.startswith("REPLACE_")


@lru_cache
def get_settings() -> Settings:
    return Settings()
