import os
import requests
import base64
from src.util.logger import log


class GitHubService:
    def __init__(self):
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.api_base = "https://api.github.com"

    def get_pr_files(self, repo_full_name: str, pr_number: int):
        try:
            url = f"{self.api_base}/repos/{repo_full_name}/pulls/{pr_number}/files"
            headers = {"Accept": "application/vnd.github.v3+json"}
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"

            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            log.error(f"GitHubService.get_pr_files error: {e}")
            return None

    def download_blob(self, repo_full_name: str, sha: str) -> str | None:
        try:
            url = f"{self.api_base}/repos/{repo_full_name}/git/blobs/{sha}"
            headers = {}
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"

            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            blob = resp.json()
            return base64.b64decode(blob.get("content", "")).decode("utf-8")
        except Exception as e:
            log.error(f"GitHubService.download_blob error: {e}")
            return None

    def build_files_content(self, repo_full_name: str, files: list) -> dict:
        files_content = {}
        for f in files:
            sha = f.get("sha")
            filename = f.get("filename")
            if not sha or not filename:
                continue
            content = self.download_blob(repo_full_name, sha)
            if content is None:
                continue
            files_content[filename] = content
        return files_content
