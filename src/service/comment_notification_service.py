import os
import requests
from src.util.logger import log


class CommentNotificationService:
    """Posts comments on GitHub pull requests."""

    def __init__(self):
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.github_api_base = "https://api.github.com"

    def post_comment(self, repo_full_name: str, pr_number: int, comment_text: str) -> bool:
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
