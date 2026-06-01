from datetime import datetime, timedelta, timezone

import jwt
from flask import current_app, request
from werkzeug.security import check_password_hash

from webiste.app.extensions import db
from webiste.app.helpers.responses import error_response, success_response
from webiste.app.models.login import Login
from webiste.app.models.user import User


def login():
    payload = request.get_json(silent=True) or {}
    username = payload.get("username")
    password = payload.get("password")

    if not username or not password:
        return error_response("username y password son requeridos", 422)

    user = User.query.filter_by(username=username).first()
    if user is None:
        return error_response("Credenciales invalidas", 401)

    # Soporta passwords hasheadas con werkzeug y texto plano (desarrollo)
    password_ok = (
        check_password_hash(user.password, password)
        if user.password.startswith(("pbkdf2:", "scrypt:", "$2b$"))
        else user.password == password
    )
    if not password_ok:
        return error_response("Credenciales invalidas", 401)

    secret = current_app.config["JWT_SECRET_KEY"]
    exp_hours = current_app.config.get("JWT_EXPIRATION_HOURS", 24)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=exp_hours)

    token = jwt.encode(
        {"sub": str(user.id), "role": user.role, "exp": expires_at},
        secret,
        algorithm="HS256",
    )

    db.session.add(Login(token=token, id_user=user.id, time=str(exp_hours * 3600)))
    db.session.commit()

    return success_response(
        {"token": token, "expires_at": expires_at.isoformat(), "user": user.to_dict()},
        "Login exitoso",
        201,
    )


def logout():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return error_response("Token requerido", 401)

    token = auth_header.removeprefix("Bearer ").strip()
    Login.query.filter_by(token=token).delete()
    db.session.commit()

    return success_response(message="Logout exitoso")
