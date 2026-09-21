from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    judge_confidence_threshold: float = 0.75

    # Tencent Cloud DB placeholders - see backend/.env.example
    tencent_db_host: str = "REPLACE_WITH_TENCENT_DB_HOST"
    tencent_db_port: int = 5432
    tencent_db_user: str = "REPLACE_ME"
    tencent_db_password: str = "REPLACE_ME"
    tencent_db_name: str = "ryde_disputes"
    tencent_db_ssl: str = "require"

    llm_provider: str = "mock"
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = "gpt-4o-mini"

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
