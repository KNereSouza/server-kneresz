from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    ADMIN_GITHUB_ID: int

    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    R2_ENDPOINT: str
    R2_ACCESS_KEY: str
    R2_SECRET_KEY: str
    R2_BUCKET: str
    R2_PUBLIC_URL: str

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
