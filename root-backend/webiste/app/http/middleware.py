import json
import time
from uuid import uuid4

import jwt
from flask import g, request

from webiste.app.extensions import db
from webiste.app.helpers.responses import error_response


PUBLIC_ENDPOINTS = {
    "api.health",
    "api.ping",
    "api.database_ping",
    "api.auth_login",
    "api.auth_register",
    "api.auth_forgot_password",
    "api.list_audios",
    "api.stream_audio",
}

# Endpoints de monitoreo: no aportan al historial de acciones de usuario
AUDIT_SKIP_ENDPOINTS = {
    "api.health",
    "api.ping",
    "api.database_ping",
}

AUTH_ENDPOINTS = {
    "api.auth_login",
    "api.auth_register",
    "api.auth_forgot_password",
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
            return error_response("Authorization Bearer token requerido", 401)

        token = auth_header.removeprefix("Bearer ").strip()
        try:
            payload = jwt.decode(
                token,
                app.config["JWT_SECRET_KEY"],
                algorithms=["HS256"],
            )
            g.current_user = payload
        except jwt.ExpiredSignatureError:
            return error_response("Token expirado", 401)
        except jwt.InvalidTokenError:
            return error_response("Token invalido", 401)

        return None

    @app.after_request
    def add_response_headers(response):
        elapsed_ms = int((time.perf_counter() - g.get("started_at", time.perf_counter())) * 1000)
        response.headers["X-Request-ID"] = g.get("request_id", "")
        response.headers["X-Response-Time-ms"] = str(elapsed_ms)
        return response

    def _resolve_actor():
        """Identifica al usuario del request: g.current_user, Bearer token
        o el query param ?token= (los tags <audio> del navegador no pueden
        enviar headers, así que el stream manda el token por URL).

        Decodifica el token incluso con AUTH_REQUIRED=false para que el
        historial atribuya acciones también en desarrollo.
        """
        payload = g.get("current_user")
        if not payload:
            token = None
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.removeprefix("Bearer ").strip()
            elif request.args.get("token"):
                token = request.args["token"]
            if token:
                try:
                    payload = jwt.decode(
                        token,
                        app.config["JWT_SECRET_KEY"],
                        algorithms=["HS256"],
                    )
                except jwt.InvalidTokenError:
                    payload = None
        if payload:
            return payload.get("sub"), payload.get("username")
        return None, None

    @app.after_request
    def audit_log(response):
        endpoint = request.endpoint
        if (
            request.method == "OPTIONS"
            or endpoint is None
            or endpoint in AUDIT_SKIP_ENDPOINTS
        ):
            return response

        from webiste.app.models.user import User
        from webiste.app.models.user_log import UserLog

        try:
            user_id, username = _resolve_actor()
            detail = None

            if endpoint in AUTH_ENDPOINTS:
                # Nunca registrar la contraseña; solo el email usado
                body = request.get_json(silent=True) or {}
                email = (body.get("email") or "").strip().lower()
                if email:
                    detail = json.dumps({"email": email})
                    # En login/register exitosos no hay token aún: atribuir por email
                    if user_id is None and response.status_code < 300:
                        user = User.query.filter_by(email=email).first()
                        if user:
                            user_id, username = str(user.id), user.username
            elif request.view_args:
                detail = json.dumps(request.view_args)

            db.session.add(UserLog(
                id_user=user_id,
                username=username,
                action=(endpoint or "").removeprefix("api."),
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                ip=request.headers.get("X-Forwarded-For", request.remote_addr),
                user_agent=(request.user_agent.string or "")[:300],
                detail=detail,
            ))
            db.session.commit()
        except Exception:  # noqa: BLE001 - el log nunca debe romper la respuesta
            db.session.rollback()
            app.logger.exception("No se pudo registrar el log de auditoria")

        return response
