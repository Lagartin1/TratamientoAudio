from flask import Blueprint

from webiste.app.controllers.auth_controller import login, logout
from webiste.app.controllers.audios_controller import get_audio, list_audios
from webiste.app.controllers.birds_controller import list_birds
from webiste.app.controllers.diagnostics_controller import database_ping, ping
from webiste.app.controllers.health_controller import health


api_bp = Blueprint("api", __name__)

# Infraestructura
api_bp.add_url_rule("/health", "health", health, methods=["GET"])
api_bp.add_url_rule("/ping", "ping", ping, methods=["GET"])
api_bp.add_url_rule("/db/ping", "database_ping", database_ping, methods=["GET"])

# Auth
api_bp.add_url_rule("/auth/login", "auth_login", login, methods=["POST"])
api_bp.add_url_rule("/auth/logout", "auth_logout", logout, methods=["POST"])

# Datos de audio y aves (para el mapa de ruido del public-frontend)
api_bp.add_url_rule("/audios", "list_audios", list_audios, methods=["GET"])
api_bp.add_url_rule("/audios/<string:audio_id>", "get_audio", get_audio, methods=["GET"])
api_bp.add_url_rule("/birds", "list_birds", list_birds, methods=["GET"])
