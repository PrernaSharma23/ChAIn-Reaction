import os
import requests
from src.util.logger import log


class CommentNotificationService:
    """Posts comments on GitHub pull requests."""

    def __init__(self):
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.github_api_base = "https://api.github.com"

    def post_acknowledgement(self, repo_full_name: str, pr_number: int) -> bool:
        msg = (
            "## 🔗 ChAIn Reaction In Progress\n\n"
            "Thanks for triggering impact analysis! I'm now analyzing the dependencies and changes in this pull request.\n\n"
            "**What I'm doing**\n"
            "- 📊 Comparing your changes against the dependency graph\n"
            "- 🔄 Tracing impact propagation across repositories\n"
            "**Expected completion**\n"
            "You'll receive an impact report shortly.\n\n"
            "Stand by... 🚀"
        )
        return self.post_impact_comment(repo_full_name, pr_number, msg)

    def post_error_comment(self, repo_full_name: str, pr_number: int, error_message: str) -> bool:
        msg = (
            "## ❌ ChAIn Reaction Analysis Error\n\n"
            f"An error occurred while analyzing this pull request:\n\n"
            f"```\n{error_message}\n```\n\n"
            "If the issue persists, contact support.*\n"
        )
        return self.post_impact_comment(repo_full_name, pr_number, msg)

    def post_no_impact_comment(self, repo_full_name: str, pr_number: int) -> bool:
        msg = (
            "## ✅ Impact Analysis — No Impact Detected\n\n"
            "I ran static dependency and graph-based analysis for the changes in this pull request and did not find any upstream/downstream or transitive impacts within the repositories onboarded onto ChAIn-Reaction Platform.\n\n"
            "**What this means**\n"
            "- The modified files did not introduce or modify graph nodes that affect other tracked components.\n\n"
            "**If you expected impact**\n"
            "- Ensure the repository is onboarded and up-to-date in the system.\n"
            "- Consider whether the impact analysis scope (intra-repo vs. cross-repo) matches your expectations.\n"
            "- Trigger a re-analysis by commenting: `@ChAIn-Reaction-Bot : Cross-Repo Impact`\n\n"
        )
        return self.post_impact_comment(repo_full_name, pr_number, msg)

    def post_impact_comment(self, repo_full_name: str, pr_number: int, comment_text: str) -> bool:
        """
        Post a comment on a PR.
        repo_full_name: e.g., "PrernaSharma23/ChAIn-Reaction"
        pr_number: PR number, e.g., 1
        comment_text: Comment body (supports markdown)
        Returns True on success, False on error.
        """
        if not self.github_token:
            log.error("GITHUB_TOKEN not configured; cannot post comments")
            return False

        try:
            url = f"{self.github_api_base}/repos/{repo_full_name}/issues/{pr_number}/comments"
            headers = {
                "Authorization": f"Bearer {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
            }
            payload = {"body": comment_text}

            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            log.info(f"Posted comment on {repo_full_name}#{pr_number}")
            return True
        except Exception as e:
            log.error(f"Error posting comment: {e}")
            return False
