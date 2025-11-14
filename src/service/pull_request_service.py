import os
import requests
from src.util.logger import log
from src.service.comment_notification_service import CommentNotificationService


class PullRequestService:
   

    def __init__(self):
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.notification_service = CommentNotificationService()

    def get_pr_diff(self, repo_full_name: str, pr_number: int) -> str | None:
        try:
            url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}"
            headers = {}
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"
            headers["Accept"] = "application/vnd.github.v3.diff"

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            log.error(f"Error fetching PR diff: {e}")
            return None

    def analyze_diff(self, diff_content: str) -> dict:
        """
        Analyze diff and extract changed files/functions.
        Returns a dict with analysis results.
        """
        try:
            # TODO: implement detailed diff parsing using tree-sitter
            # For now, just count changed files
            lines = diff_content.split("\n")
            changed_files = [line for line in lines if line.startswith("diff --git")]
            log.info(f"Found {len(changed_files)} changed files in diff")
            return {
                "changed_files": len(changed_files),
                "analysis": "pending",
            }
        except Exception as e:
            log.error(f"Error analyzing diff: {e}")
            return {"error": str(e)}

    def analyze_pr(self, repo_full_name: str, pr_number: int) -> dict:
        try : 
            log.info(f"Analyzing PR {repo_full_name}#{pr_number}")
            diff = self.get_pr_diff(repo_full_name, pr_number)
            if not diff:
                return {"error": "Could not fetch PR diff"}
            result = self.analyze_diff(diff)
            
            # Post analysis result as comment on PR
            if result:
                # Format result as markdown comment
                result_comment = f"## 🔗 ChAIn Reaction Analysis Results\n\n{str(result)}\n\n*Analysis complete.*"
                self.notification_service.post_comment(repo_full_name, pr_number, result_comment)
            return result
        except Exception as e:
            log.error(f"Error analyzing PR: {e}")
            error_comment = f"## 🔗 ChAIn Reaction Analysis Error\n\n{str(e)}\n\n*Analysis failed.*"
            self.notification_service.post_comment(repo_full_name, pr_number, error_comment)

