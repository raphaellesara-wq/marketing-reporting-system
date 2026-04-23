from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    app_name: str = "MarketingReportingSaaS"
    app_env: str = "development"
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    database_url: str = "postgresql://mruser:mrpassword@postgres:5432/marketing_reporting"
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    upload_dir: str = "/app/uploads"
    reports_dir: str = "/app/reports"

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()
