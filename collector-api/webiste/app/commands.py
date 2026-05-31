from pathlib import Path

import click
from flask import current_app
from flask.cli import with_appcontext

from webiste.app.extensions import db


@click.command("init-db")
@with_appcontext
def init_db_command():
    from webiste.app import models  # noqa: F401

    db.create_all()
    click.echo("Database tables created.")


@click.command("init-sql")
@with_appcontext
def init_sql_command():
    if db.engine.dialect.name != "postgresql":
        raise click.ClickException("init-sql is only available for PostgreSQL/Supabase connections.")

    schema_path = Path(current_app.root_path) / "sql" / "init_schema.sql"
    statements = [
        statement.strip()
        for statement in schema_path.read_text(encoding="utf-8").split(";")
        if statement.strip()
    ]

    with db.engine.begin() as connection:
        for statement in statements:
            connection.exec_driver_sql(statement)

    click.echo(f"SQL schema initialized from {schema_path}.")


def register_commands(app):
    app.cli.add_command(init_db_command)
    app.cli.add_command(init_sql_command)
