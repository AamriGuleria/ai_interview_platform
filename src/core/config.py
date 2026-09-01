from pydantic_settings import BaseSettings, SettingsConfigDict
# python -m services.dataset_builder.exporter.csv_exporter
# python -m scripts.create_embeddings

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
    # rabbitmq_url : str = "amqp://admin:admin123@localhost:5672//"
    postgres_result_backend : str = "db+postgresql://admin:admin123@localhost:5432/mydatabase"
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
    secure: bool = False
    bucket_name: str = "resume"
    gemini_api_key: str = "hello"
    question_evaluation_mode: str = "overall"
    max_follow_ups_per_interview: int = 3
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "admin"
    rabbitmq_password: str = "admin123"
    redis_port: int = 6379
    redis_db: int = 0
    rabbitmq_host: str = "rabbitmq"
    redis_host: str = "redis"
    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}//"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
config = Config()
