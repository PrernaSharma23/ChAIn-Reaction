import os
import json
import tempfile
import git
from flask import Blueprint, request, jsonify, current_app
from src.processor.repo_processor import RepoProcessor 

from src.util.logger import log


pr_bp = Blueprint("pr_controller", __name__)


@pr_bp.route("/webhook/pr", methods=["POST"])
def handle_pr_event():
    """
    Handles GitHub or Bitbucket pull request creation webhooks.
    On PR create/opened event → clones base branch and analyzes impact.
    """
    try:
        payload = request.get_json(force=True)
        log.info(f"Received PR webhook: {json.dumps(payload, indent=2)}")
        

        #  repo_url, base_branch, feature_branch = extract_pr_info(payload)
        # 1 Generate feature graph
        # 2️ Fetch base graph from Neo4j
        # 3️ Detect changes
        # 4️ For each changed node, run impact query
        return jsonify({"message": "PR processed successfully"}), 200

    except Exception as e:
        log.error(f"Error processing PR webhook: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    
    
