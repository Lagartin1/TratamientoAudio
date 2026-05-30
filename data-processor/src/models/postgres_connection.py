import os
from contextlib import contextmanager
from typing import Any, Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DATABASE_URL_ENV_VARS = ("SUPABASE_DB_URL", "DATABASE_URL", "POSTGRES_URL")

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


class Base(DeclarativeBase):
    pass


def get_database_url() -> str:
    """
    Obtiene la URL de conexion a Postgres/Supabase desde variables de entorno.
    """
    for env_var in DATABASE_URL_ENV_VARS:
        database_url = os.getenv(env_var)
        if database_url:
            return database_url

    env_names = ", ".join(DATABASE_URL_ENV_VARS)
    raise RuntimeError(
        f"No se encontro URL de Postgres. Define una de estas variables: {env_names}"
    )


def get_sqlalchemy_database_url() -> str:
    """
    Convierte la URL de Supabase al dialecto SQLAlchemy para psycopg v3.
    """
    database_url = get_database_url()

    if database_url.startswith("postgresql+psycopg://"):
        return database_url
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)

    return database_url


def get_engine() -> Engine:
    """
    Crea y reutiliza el engine SQLAlchemy para Supabase Postgres.
    """
    global _engine

    if _engine is None:
        _engine = create_engine(
            get_sqlalchemy_database_url(),
            pool_pre_ping=True,
            pool_size=int(os.getenv("POSTGRES_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("POSTGRES_MAX_OVERFLOW", "10")),
        )

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
