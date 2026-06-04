from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def DATABASE_URL(self) -> str:
        return self.database_url

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return self.async_database_url
    database_url: str = "postgresql://user:password@localhost:5432/db_name"
    async_database_url: str = "postgresql+asyncpg://user:password@localhost:5432/db_name"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_recycle: int = 3600
    pool_pre_ping: bool = True
    pool_use_lifo: bool = True
    jwt_secret_key: str = "default"
    algorithm: str = "HS256"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    secure: str = False
    bucket_name: str = "resume"
config = Config()
