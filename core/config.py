from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    DEBUG: bool = False
    REDIS_HOST: str = '127.0.0.1'
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = 'password'
    POSTGRES_HOST: str = '127.0.0.1'
    POSTGRES_USER: str = 'user'
    POSTGRES_PASSWORD: str = 'password'
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = 'db'

    APP_TITLE: str= "FastAPI App"
    APP_VERSION: str= "1.0"


    SHEDULER_PROCESSPOOL_MAX_WORKERS: int = 1

    @property
    def DATABASE_URL(self) -> str:
        return (f'postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}'
                    f'@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}')

    @property
    def REDIS_URL(self) -> str:
        return f'redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}'

    @property
    def CELERY_BROKER_URL(self) -> str:
        return f'redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0'

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return f'redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0'

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra='allow'
    )

settings = Settings()