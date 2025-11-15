import os
from flask import Blueprint, request, jsonify
from src.service.project_service import ProjectService
from src.service.user_service import UserService
from src.util.logger import log
from src.util.async_tasks import run_async

project_blueprint = Blueprint("project_controller", __name__)
service = ProjectService()
user_service = UserService()


@project_blueprint.route("/onboard", methods=["POST"])
def onboard_project():
    """
    Called by UI when a new GitHub project is onboarded.
    Payload: {"repo_name": "java_repo", "repo_url": "https://github.com/user/repo.git" }
    """
    log.info("Onboarding new project")
    data = request.get_json() or {}
    repo_url = data.get("repo_url")
    repo_name = data.get("repo_name")
    # require user to be logged in
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "Authorization token required"}), 401

    token = auth.split(" ", 1)[1].strip()
    decoded = user_service.decode_token(token)
    if isinstance(decoded, dict) and decoded.get("error"):
        return jsonify(decoded), 401

    user_id = decoded.get("sub")
    if not repo_url:
        return jsonify({"error": "repo_url missing"}), 400

    repo = user_service.add_repository_to_user(user_id, repo_url, repo_name)
    run_async(service.process_repository, repo["repo_name"], repo["repo_url"])
    out = {"saved_repo": repo, "message": "Repository onboarded and processing started asynchronously"}
    return jsonify(out), 200


# CRUD endpoints for UI
@project_blueprint.route("/nodes", methods=["GET"])
def get_nodes():
    nodes = service.get_all_nodes()
    return jsonify(nodes), 200


@project_blueprint.route("/edges", methods=["GET"])
def get_edges():
    edges = service.get_all_edges()
    return jsonify(edges), 200


@project_blueprint.route("/clear", methods=["DELETE"])
def clear_graph():
    service.clear_graph()
    return jsonify({"message": "Graph cleared"}), 200
