from flask import Blueprint

from webiste.app.controllers.diagnostics_controller import database_ping, ping
from webiste.app.controllers.example_controller import (
    forced_exception_example,
    get_example,
    list_examples,
    validate_payload_example,
)
from webiste.app.controllers.health_controller import health

from webiste.app.controllers.users_controller import create_user, list_users
from webiste.app.controllers.upload_audio_controller import upload_audio


api_bp = Blueprint("api", __name__)

api_bp.add_url_rule("/health", "health", health, methods=["GET"])
api_bp.add_url_rule("/ping", "ping", ping, methods=["GET"])
api_bp.add_url_rule("/db/ping", "database_ping", database_ping, methods=["GET"])

api_bp.add_url_rule("/examples", "list_examples", list_examples, methods=["GET"])
api_bp.add_url_rule("/examples/<int:example_id>", "get_example", get_example, methods=["GET"])
api_bp.add_url_rule(
    "/examples/validate",
    "validate_payload_example",
    validate_payload_example,
    methods=["POST"],
)
api_bp.add_url_rule(
    "/examples/force-error",
    "forced_exception_example",
    forced_exception_example,
    methods=["GET"],
)

api_bp.add_url_rule("/users", "list_users", list_users, methods=["GET"])
api_bp.add_url_rule("/users", "create_user", create_user, methods=["POST"])

# Nuevo endpoint para subir audio y metadatos
api_bp.add_url_rule("/upload-audio", "upload_audio", upload_audio, methods=["POST"])
