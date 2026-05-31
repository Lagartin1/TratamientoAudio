from flask import request

from webiste.app.extensions import db
from webiste.app.helpers.responses import error_response, success_response
from webiste.app.models import User


def list_users():
    users = User.query.order_by(User.name.asc()).all()
    return success_response([user.to_dict() for user in users])


def create_user():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name")
    username = payload.get("username")
    password = payload.get("password")
    role = payload.get("role")

    if not name or not username or not password or not role:
        return error_response("name, username, password and role are required", 422)

    if User.query.filter_by(username=username).first():
        return error_response("username already exists", 409)

    user = User(name=name, username=username, password=password, role=role)
    db.session.add(user)
    db.session.commit()

    return success_response(user.to_dict(), "User created", 201)
