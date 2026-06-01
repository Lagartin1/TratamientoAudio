from os import getenv
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class BaseConfig:
    APP_HOST = getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(getenv("APP_PORT", "5000"))
    SECRET_KEY = getenv("SECRET_KEY", "change-me")

    _db_user = getenv("user")
    _db_password = getenv("password")
    _db_host = getenv("host")
    _db_port = getenv("port", "5432")
    _db_name = getenv("dbname", "postgres")

    if _db_user and _db_password and _db_host:
        _constructed_db_url = f"postgresql://{_db_user}:{_db_password}@{_db_host}:{_db_port}/{_db_name}"
        SQLALCHEMY_DATABASE_URI = _constructed_db_url
        SUPABASE_DB_URL = _constructed_db_url
    else:
        SQLALCHEMY_DATABASE_URI = getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'database.db'}")
        SUPABASE_DB_URL = getenv("SUPABASE_DB_URL", getenv("DATABASE_URL"))

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SUPABASE_URL = getenv("SUPABASE_URL")
    SUPABASE_KEY = getenv("SUPABASE_KEY")

    AUTH_REQUIRED = getenv("AUTH_REQUIRED", "false").lower() == "true"
    CORS_ORIGINS = getenv("CORS_ORIGINS", "*").split(",")

    JSON_SORT_KEYS = False
    # Redis settings for enqueuing audio processing jobs
    REDIS_URL = getenv("REDIS_URL", None)
    REDIS_QUEUE = getenv("REDIS_QUEUE", "audio_jobs")


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
