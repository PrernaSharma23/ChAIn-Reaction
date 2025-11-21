import os
import json
import hmac
import hashlib
from flask import Blueprint, request, jsonify
from src.service.pull_request_service import PullRequestService
from src.service.comment_notification_service import CommentNotificationService
from src.util.logger import log
from src.util.async_tasks import run_async

pr_bp = Blueprint("pr_controller", __name__)
pr_service = PullRequestService()
notification_service = CommentNotificationService()

ACTIVE_ANALYSES: set = set()

TRIGGER_PHRASES = [
    "@ChAIn-Reaction-Bot",
    "@chain-reaction-bot : start analysis",
    "@chain-reaction-bot : analyze pr",
    "@chain-reaction-bot : analyze impact",
    "@chain-reaction-bot analyze impact",
    "@chain-reaction : start analysis",
    "@chain-reaction : analyze impact",
    "@chain-reaction : analyze pr",
    "@chain-reaction",
    "chain-reaction",
    "start analysis",
    "check impact",
    "analyze impact",
    "trigger chain reaction",
    "check chain reaction",
    "chain reaction",
    "start chain reaction",
    "analyze chain reaction",
    "trigger impact analysis",
    "trigger analysis",
    "run analysis",
    "analyze pr",
    "start impact analysis",
    "check pr impact",
]

EXTERNAL_TRIGGER_PHRASES = [
    "@ChAIn-Reaction-Bot : cross-repo impact",
    "@chain-reaction-bot : external impact",
    "@chain-reaction-bot : external-only",
    "cross-repo impact",
    "cross repo impact",
    "external impact",
    "impact other repos",
    "external-only",
    "cross-repo",
]


def _verify_signature(secret: str, body: bytes, signature: str) -> bool:
    if not secret or not signature:
        return False
    
    expected = signature.split("=", 1)[1] if "=" in signature else signature
    mac = hmac.new(secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), expected)


def _is_trigger_phrase(comment_body: str) -> bool:
    if not comment_body:
        return False
    
    comment_lower = comment_body.lower()
    return comment_lower in TRIGGER_PHRASES

def _is_external_trigger(comment_body: str) -> bool:
    if not comment_body:
        return False
    cl = comment_body.lower()
    return cl in EXTERNAL_TRIGGER_PHRASES

def _run_and_manage(repo_name, pr_no, clone_url, key, external_only: bool = False):
    ACTIVE_ANALYSES.add(key)
    try:
        pr_service.analyze_pr(repo_name, pr_no, clone_url, external_only)
    finally:
        try:
            ACTIVE_ANALYSES.remove(key)
        except KeyError:
            pass


@pr_bp.route("/webhook/pr", methods=["POST"])
def handle_pr_event():
    try:
        raw_body = request.get_data()
        
        secret = os.environ.get("GITHUB_WEBHOOK_SECRET")
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not secret or not _verify_signature(secret, raw_body, signature):
            log.warning("Invalid webhook signature")
            return jsonify({"error": "invalid_signature"}), 401
        
        payload = json.loads(raw_body)
        
        event = request.headers.get("X-GitHub-Event")
        action = payload.get("action")
        if event != "issue_comment" or action != "created":
            log.info(f"Skipping event={event} action={action}")
            return jsonify({"message": "ignored"}), 200
        
        issue = payload.get("issue", {})
        if not issue.get("pull_request"):
            log.info("Not a PR, skipping")
            return jsonify({"message": "ignored"}), 200
        
        comment = payload.get("comment", {})
        comment_body = comment.get("body", "")

        if not (_is_trigger_phrase(comment_body) or _is_external_trigger(comment_body)):
            return jsonify({"message": "ignored"}), 200
        

        repo = payload.get("repository", {})
        repo_full_name = repo.get("full_name")
        pr_number = issue.get("number")
        clone_url = repo.get("clone_url") 
        
        if not repo_full_name or not pr_number:
            log.warning("Missing repo or PR number")
            return jsonify({"error": "missing_info"}), 400
        
        key = f"{repo_full_name}#{pr_number}"
        if key in ACTIVE_ANALYSES:
            log.info(f"Analysis already in progress for {key}, skipping")
            return jsonify({"message": "already_in_progress"}), 200
        
        run_async(notification_service.post_acknowledgement, repo_full_name, pr_number)

        external_only = _is_external_trigger(comment_body)

        run_async(_run_and_manage, repo_full_name, pr_number, clone_url, key, external_only)
        log.info(f"Queued analysis for {repo_full_name}#{pr_number} (external_only={external_only})")

        return jsonify({"message": "queued"}), 202
        
    except json.JSONDecodeError:
        log.error("Invalid JSON in webhook")
        return jsonify({"error": "invalid_json"}), 400
    except Exception as e:
        log.error(f"Error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


