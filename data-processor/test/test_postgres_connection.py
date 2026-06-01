from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool

from models import postgres_connection


def _disable_real_env_file(monkeypatch):
    monkeypatch.setattr(postgres_connection, "_local_env_loaded", True)


def _clear_database_env(monkeypatch):
    env_vars = set(postgres_connection.DATABASE_URL_ENV_VARS)
    for component_env_vars in postgres_connection.DATABASE_COMPONENT_ENV_VARS.values():
        env_vars.update(component_env_vars)

    for env_var in env_vars:
        monkeypatch.delenv(env_var, raising=False)


def test_builds_supabase_pooler_url_from_component_env(monkeypatch):
    _disable_real_env_file(monkeypatch)
    _clear_database_env(monkeypatch)

    monkeypatch.setenv("user", "postgres.bbmkxrvvyxboiihylcdt")
    monkeypatch.setenv("password", "pa:ss/word")
    monkeypatch.setenv("host", "aws-1-us-east-2.pooler.supabase.com")
    monkeypatch.setenv("port", "5432")
    monkeypatch.setenv("dbname", "postgres")

    database_url = postgres_connection.get_sqlalchemy_database_url()
    url = make_url(database_url)

    assert url.drivername == "postgresql+psycopg"
    assert url.username == "postgres.bbmkxrvvyxboiihylcdt"
    assert url.password == "pa:ss/word"
    assert url.host == "aws-1-us-east-2.pooler.supabase.com"
    assert url.port == 5432
    assert url.database == "postgres"
    assert url.query["sslmode"] == "require"


def test_converts_psycopg2_url_to_installed_psycopg_driver(monkeypatch):
    _disable_real_env_file(monkeypatch)
    _clear_database_env(monkeypatch)

    monkeypatch.setenv(
        "SUPABASE_DB_URL",
        "postgresql+psycopg2://user:pass@example.com:5432/postgres",
    )

    database_url = postgres_connection.get_sqlalchemy_database_url()

    assert make_url(database_url).drivername == "postgresql+psycopg"


def test_detects_supabase_pooler_urls():
    assert postgres_connection._uses_supabase_pooler(
        "postgresql+psycopg://user:pass@"
        "aws-1-us-east-2.pooler.supabase.com:5432/postgres"
    )
    assert not postgres_connection._uses_supabase_pooler(
        "postgresql+psycopg://user:pass@db.example.com:5432/postgres"
    )


def test_supabase_pooler_engine_uses_null_pool(monkeypatch):
    _disable_real_env_file(monkeypatch)
    _clear_database_env(monkeypatch)
    monkeypatch.setenv(
        "SUPABASE_DB_URL",
        "postgresql://user:pass@aws-1-us-east-2.pooler.supabase.com:5432/postgres",
    )
    monkeypatch.setattr(postgres_connection, "_engine", None)
    monkeypatch.setattr(postgres_connection, "_session_factory", None)

    engine = postgres_connection.get_engine()

    try:
        assert isinstance(engine.pool, NullPool)
    finally:
        engine.dispose()
        monkeypatch.setattr(postgres_connection, "_engine", None)
