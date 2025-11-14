from flask import Blueprint, request, jsonify
from src.service.user_service import UserService
from src.util.logger import log

user_blueprint = Blueprint("user_controller", __name__)
service = UserService()


@user_blueprint.route("/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    username = data.get("username")
    name = data.get("name")
    password = data.get("password")
    if not username or not name or not password:
        return jsonify({"error": "username, name and password required"}), 400

    result = service.signup(username, name, password)
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result), 201


@user_blueprint.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    result = service.login(username, password)
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result), 200


@user_blueprint.route("/profile", methods=["GET"])
def profile():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "missing token"}), 401

    token = auth.split(" ", 1)[1].strip()
    decoded = service.decode_token(token)
    if isinstance(decoded, dict) and decoded.get("error"):
        return jsonify(decoded), 401

    user_id = decoded.get("sub")
    profile = service.get_profile(user_id)
    if not profile:
        return jsonify({"error": "user not found"}), 404

    return jsonify(profile), 200
