import time
from uuid import uuid4

from flask import g, request

from webiste.app.helpers.responses import error_response
from webiste.app.services.supabase_service import get_supabase_service


PUBLIC_ENDPOINTS = {
    "api.database_ping",
    "api.health",
    "api.ping",
}


def register_middlewares(app):
    @app.before_request
    def attach_request_context():
        g.request_id = request.headers.get("X-Request-ID", str(uuid4()))
        g.started_at = time.perf_counter()

    @app.before_request
    def authenticate_request():
        if not app.config.get("AUTH_REQUIRED", False):
            return None

        if request.endpoint in PUBLIC_ENDPOINTS:
            return None

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return error_response("Authorization Bearer token is required", 401)

        token = auth_header.removeprefix("Bearer ").strip()
        try:
            g.current_user = get_supabase_service(app).get_user_from_token(token)
        except Exception:
            return error_response("Invalid or expired token", 401)

        return None

    @app.after_request
    def add_response_headers(response):
        elapsed_ms = int((time.perf_counter() - g.get("started_at", time.perf_counter())) * 1000)
        response.headers["X-Request-ID"] = g.get("request_id", "")
        response.headers["X-Response-Time-ms"] = str(elapsed_ms)
        return response
