import os
from flask import Blueprint, request, jsonify, g
from src.service.project_service import ProjectService
from src.service.user_service import UserService
from src.util.logger import log
from src.util.async_tasks import run_async
from src.util.auth import jwt_required

project_blueprint = Blueprint("project_controller", __name__)
service = ProjectService()
user_service = UserService()


@project_blueprint.route("/onboard", methods=["POST"])
@jwt_required
def onboard_project():
    """
    Called by UI when a new GitHub project is onboarded.
    Payload: {"repo_name": "java_repo", "repo_url": "https://github.com/user/repo.git" }
    """
    log.info("Onboarding new project")
    data = request.get_json() or {}
    repo_url = data.get("repo_url")
    repo_name = data.get("repo_name")
    user_id = g.user.get("sub")
    if not repo_url:
        return jsonify({"error": "repo_url missing"}), 400

    repo = user_service.add_repository_to_user(user_id, repo_url, repo_name)
    if repo and repo.get("is_new"):
        run_async(service.process_repository, repo["id"], repo["repo_name"], repo["repo_url"])
        msg = "Repository onboarded and processing started asynchronously"
    else:
        msg = "Repository added to user (already exists in system)"
    out = {"saved_repo": repo, "message": msg}
    return jsonify(out), 200

@project_blueprint.route("/graph", methods=["POST"])
@jwt_required
def get_graph_for_repos():
    """
    POST body: {"repo_ids": ["repo_id1", "repo_id2", ...]}
    Returns { "nodes": [...], "edges": [...] }
    """
    data = request.get_json() or {}
    repo_ids = data.get("repo_ids")
    if not isinstance(repo_ids, list) or not repo_ids:
        return jsonify({"error": "repo_ids must be a non-empty list"}), 400

    try:
        result = service.get_graph_for_repos(repo_ids)
        return jsonify(result), 200
    except Exception as e:
        log.error(f"Error fetching graph for repos {repo_ids}: {e}")
        return jsonify({"error": str(e)}), 500


@project_blueprint.route("/edge", methods=["POST"])
@jwt_required
def create_edge():
    """Create a relationship between two existing nodes.

    Expected JSON body: { "from": "uid1", "to": "uid2", "type": "DEPENDS_ON" }
    Returns { ok: true } or { error: ... }
    """
    data = request.get_json() or {}
    src = data.get("from")
    dst = data.get("to")
    edge_type = data.get("type")

    if not src or not dst or not edge_type:
        return jsonify({"error": "from, to and type are required"}), 400
    try:
        res = service.create_relationship(src, dst, edge_type)
        if res.get("error"):
            return jsonify(res), 400
        return jsonify(res), 200
    except Exception as e:
        log.error(f"Error creating edge {src}->{dst} ({edge_type}): {e}")
        return jsonify({"error": str(e)}), 500
 
@project_blueprint.route("/nodes", methods=["GET"])
@jwt_required
def get_nodes():
    nodes = service.get_all_nodes()
    return jsonify(nodes), 200


@project_blueprint.route("/edges", methods=["GET"])
@jwt_required
def get_edges():
    edges = service.get_all_edges()
    return jsonify(edges), 200


@project_blueprint.route("/clear", methods=["DELETE"])
@jwt_required
def clear_graph():
    service.clear_graph()
    return jsonify({"message": "Graph cleared"}), 200
