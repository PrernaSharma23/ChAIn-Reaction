from flask import Blueprint, request, jsonify
from src.service.project_service import ProjectService

from src.util.logger import log

project_blueprint = Blueprint("project_controller", __name__)
service = ProjectService()

@project_blueprint.route("/onboard", methods=["POST"])
def onboard_project():
    """
    Called by UI when a new GitHub project is onboarded.
    Payload: { "repo_url": "https://github.com/user/repo.git" }
    """
    log.info("Onboarding new project")
    data = request.get_json()
    repo_url = data.get("repo_url")
    if not repo_url:
        return jsonify({"error": "repo_url missing"}), 400

    result = service.process_repository(repo_url)
    return jsonify(result), 200


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
