from flask import jsonify


def success_response(data=None, message="OK", status_code=200):
    payload = {
        "ok": True,
        "message": message,
        "data": data,
    }
    return jsonify(payload), status_code


def error_response(message="Error", status_code=400, errors=None):
    payload = {
        "ok": False,
        "message": message,
        "errors": errors,
    }
    return jsonify(payload), status_code
