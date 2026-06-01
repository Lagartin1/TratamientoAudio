import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL, make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool


DATABASE_URL_ENV_VARS = ("SUPABASE_DB_URL", "DATABASE_URL", "POSTGRES_URL")
DATABASE_COMPONENT_ENV_VARS = {
    "username": ("user", "POSTGRES_USER", "PGUSER", "SUPABASE_DB_USER"),
    "password": ("password", "POSTGRES_PASSWORD", "PGPASSWORD", "SUPABASE_DB_PASSWORD"),
    "host": ("host", "POSTGRES_HOST", "PGHOST", "SUPABASE_DB_HOST"),
    "port": ("port", "POSTGRES_PORT", "PGPORT", "SUPABASE_DB_PORT"),
    "database": ("dbname", "POSTGRES_DB", "PGDATABASE", "SUPABASE_DB_NAME"),
}
DEFAULT_POSTGRES_PORT = 5432

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None
_local_env_loaded = False


class Base(DeclarativeBase):
    pass


def load_local_env_file() -> None:
    """
    Carga src/.env si existe, sin sobrescribir variables exportadas en el entorno.
    """
    global _local_env_loaded

    if _local_env_loaded:
        return

    _local_env_loaded = True
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _get_first_env_value(env_vars: tuple[str, ...]) -> str | None:
    for env_var in env_vars:
        value = os.getenv(env_var)
        if value:
            return value

    return None


def _build_database_url_from_components() -> str | None:
    values = {
        key: _get_first_env_value(env_vars)
        for key, env_vars in DATABASE_COMPONENT_ENV_VARS.items()
    }

    if not any(values.values()):
        return None

    missing = [
        key
        for key in ("username", "password", "host", "database")
        if not values[key]
    ]
    if missing:
        missing_names = ", ".join(missing)
        raise RuntimeError(
            "Configuracion de Postgres incompleta. "
            f"Faltan estos valores: {missing_names}"
        )

    port = int(values["port"] or DEFAULT_POSTGRES_PORT)
    sslmode = os.getenv("POSTGRES_SSLMODE", "require")
    url = URL.create(
        "postgresql",
        username=values["username"],
        password=values["password"],
        host=values["host"],
        port=port,
        database=values["database"],
        query={"sslmode": sslmode},
    )

    return url.render_as_string(hide_password=False)


def get_database_url() -> str:
    """
    Obtiene la URL de conexion a Postgres/Supabase desde variables de entorno.
    """
    load_local_env_file()

    for env_var in DATABASE_URL_ENV_VARS:
        database_url = os.getenv(env_var)
        if database_url:
            return database_url

    component_database_url = _build_database_url_from_components()
    if component_database_url:
        return component_database_url

    env_names = ", ".join(DATABASE_URL_ENV_VARS)
    component_env_names = ", ".join(
        env_var
        for env_vars in DATABASE_COMPONENT_ENV_VARS.values()
        for env_var in env_vars
    )
    raise RuntimeError(
        "No se encontro configuracion de Postgres. "
        f"Define una de estas variables: {env_names}. "
        f"O define la configuracion separada: {component_env_names}"
    )


def get_sqlalchemy_database_url() -> str:
    """
    Convierte la URL de Supabase al dialecto SQLAlchemy para psycopg v3.
    """
    database_url = get_database_url()

    if database_url.startswith("postgresql+psycopg://"):
        sqlalchemy_url = database_url
    elif database_url.startswith("postgresql+psycopg2://"):
        sqlalchemy_url = database_url.replace(
            "postgresql+psycopg2://",
            "postgresql+psycopg://",
            1,
        )
    elif database_url.startswith("postgresql://"):
        sqlalchemy_url = database_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )
    elif database_url.startswith("postgres://"):
        sqlalchemy_url = database_url.replace(
            "postgres://",
            "postgresql+psycopg://",
            1,
        )
    else:
        sqlalchemy_url = database_url

    url = make_url(sqlalchemy_url)
    if _uses_supabase_pooler(sqlalchemy_url) and "sslmode" not in url.query:
        url = url.update_query_dict(
            {"sslmode": os.getenv("POSTGRES_SSLMODE", "require")}
        )

    return url.render_as_string(hide_password=False)


def _uses_supabase_pooler(database_url: str) -> bool:
    try:
        host = make_url(database_url).host or ""
    except Exception:
        return "pooler.supabase.com" in database_url

    return host.endswith(".pooler.supabase.com") or host == "pooler.supabase.com"


def get_engine() -> Engine:
    """
    Crea y reutiliza el engine SQLAlchemy para Supabase Postgres.
    """
    global _engine

    if _engine is None:
        database_url = get_sqlalchemy_database_url()
        engine_options: dict[str, Any] = {"pool_pre_ping": True}

        if _uses_supabase_pooler(database_url):
            engine_options["poolclass"] = NullPool
        else:
            engine_options["pool_size"] = int(os.getenv("POSTGRES_POOL_SIZE", "5"))
            engine_options["max_overflow"] = int(
                os.getenv("POSTGRES_MAX_OVERFLOW", "10")
            )

        _engine = create_engine(database_url, **engine_options)

    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """
    Retorna el factory de sesiones SQLAlchemy.
    """
    global _session_factory

    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            expire_on_commit=False,
        )

    return _session_factory


@contextmanager
def db_session() -> Iterator[Session]:
    """
    Context manager para consultas y transacciones con SQLAlchemy.
    Hace commit si todo sale bien y rollback si ocurre un error.
    """
    session = get_session_factory()()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def execute_query(query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """
    Ejecuta un SELECT parametrizado y retorna filas como diccionarios.
    """
    with db_session() as session:
        result = session.execute(text(query), params or {})
        return [dict(row) for row in result.mappings().all()]


def execute_statement(query: str, params: dict[str, Any] | None = None) -> int:
    """
    Ejecuta INSERT/UPDATE/DELETE parametrizado y retorna filas afectadas.
    """
    with db_session() as session:
        result = session.execute(text(query), params or {})
        return result.rowcount


def check_connection() -> bool:
    """
    Verifica que Supabase Postgres responda.
    """
    rows = execute_query("select 1 as ok")
    return bool(rows and rows[0]["ok"] == 1)


if __name__ == "__main__":
    try:
        if check_connection():
            print("Conexion a Postgres/Supabase OK")
    except Exception as exc:
        print(f"Error conectando a Postgres/Supabase: {exc}")
