from os import getenv
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _build_database_url():
    url = getenv("DATABASE_URL")
    if url:
        return url
    host = getenv("DB_HOST")
    port = getenv("DB_PORT", "5432")
    user = getenv("DB_USER")
    password = getenv("DB_PASSWORD")
    name = getenv("DB_NAME", "postgres")
    if host and user and password:
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"
    return f"sqlite:///{BASE_DIR / 'database.db'}"


class BaseConfig:
    APP_HOST = getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(getenv("APP_PORT", "4001"))
    SECRET_KEY = getenv("SECRET_KEY", "change-me")

    SQLALCHEMY_DATABASE_URI = _build_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = (
        {"connect_args": {"connect_timeout": 10}}
        if _build_database_url().startswith("postgresql")
        else {}
    )

    SUPABASE_URL = getenv("SUPABASE_URL")
    SUPABASE_KEY = getenv("SUPABASE_KEY")

    JWT_SECRET_KEY = getenv("JWT_SECRET_KEY", "change-me-jwt")
    JWT_EXPIRATION_HOURS = int(getenv("JWT_EXPIRATION_HOURS", "24"))

    AUTH_REQUIRED = getenv("AUTH_REQUIRED", "false").lower() == "true"
    # 4201 = public-frontend, 4200 = collector-frontend
    CORS_ORIGINS = getenv("CORS_ORIGINS", "http://localhost:4201,http://localhost:4200").split(",")

    JSON_SORT_KEYS = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENV = "development"


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


class ProductionConfig(BaseConfig):
    DEBUG = False
    ENV = "production"
    AUTH_REQUIRED = True


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
