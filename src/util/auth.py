from functools import wraps
from flask import request, jsonify, g
from src.util.logger import log


def get_user_service():
    from src.service.user_service import UserService
    return UserService()


def jwt_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization token required"}), 401

        token = auth_header.split(" ", 1)[1].strip()
        user_service = get_user_service()
        decoded = user_service.decode_token(token)

        if isinstance(decoded, dict) and decoded.get("error"):
            return jsonify(decoded), 401

        g.user = decoded
        return fn(*args, **kwargs)

    return wrapper
