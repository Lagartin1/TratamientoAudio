from flask import current_app, g
from sqlalchemy import text

from webiste.app.exceptions.api_exceptions import DatabaseConnectionException
from webiste.app.extensions import db
from webiste.app.helpers.responses import success_response


def ping():
    return success_response(
        {
            "pong": True,
            "request_id": g.get("request_id"),
        },
        "pong",
    )


def database_ping():
    try:
        value = db.session.execute(text("SELECT 1")).scalar()
    except Exception as error:
        current_app.logger.exception(error)
        raise DatabaseConnectionException(errors={"detail": str(error)}) from error

    return success_response(
        {
            "connected": value == 1,
            "driver": db.engine.url.drivername,
            "database": db.engine.url.database,
        },
        "Database connection OK",
    )
