import os
import requests
import base64
from src.util.logger import log
from src.service.comment_notification_service import CommentNotificationService


class PullRequestService:
   

    def __init__(self):
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.notification_service = CommentNotificationService()

    def download_file(self, repo_full_name, sha):
        """Download raw file contents from GitHub given blob SHA."""
        url = f"https://api.github.com//repos/{repo_full_name}/git/blobs/{sha}"
        headers = {"Authorization": f"token {self.github_token}"}
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        blob = resp.json()
        return base64.b64decode(blob['content']).decode('utf-8')
    
    def get_pr_diff_files(self, repo_full_name: str, pr_number: int) -> str | None:
        try:
            url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/files"
            headers = {}
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"
            headers["Accept"] = "application/vnd.github.v3.diff"

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            log.error(f"Error fetching PR diff: {e}")
            return None

    def analyze_diff(self, files_content: dict) -> dict:
        from src.processor.tree_sitter_extractor import TreeSitterExtractor

        try:
            extractor = TreeSitterExtractor()
            all_nodes, all_edges = [], []

            for file_path, content in files_content.items():
                lang = extractor.get_language(file_path)
                if not lang:
                    continue

                symbols = extractor.extract_from_string(content, file_path, lang)
                file_result = {"symbols": symbols, "language": lang}

                nodes = extractor.convert_symbols_to_nodes("repo", file_path, file_result)
                edges = extractor.derive_edges_from_symbols("repo", file_path, file_result)

                all_nodes += nodes
                all_edges += edges

            return {"nodes": all_nodes, "edges": all_edges}

        except Exception as e:
            log.error(f"Error analyzing diff: {e}")
            return {"error": str(e)}


    def analyze_pr(self, repo_full_name: str, pr_number: int) -> dict:
        try:
            log.info(f"Analyzing PR {repo_full_name}#{pr_number}")
            files = self.get_pr_diff_files(repo_full_name, pr_number)
            if not files:
                return {"nodes": [], "edges": []}

            # Prepare a dict of {filename: content} for analyze_diff
            files_content = {}
            for f in files:
                file_content = self.download_file(repo_full_name, f["sha"])
                files_content[f["filename"]] = file_content

            # Call analyze_diff to generate AST nodes and edges
            result = self.analyze_diff(files_content)

            if result.get("nodes") or result.get("edges"):
                result_comment = (
                    f"## 🔗 ChAIn Reaction Analysis Results\n\n"
                    f"Nodes: {len(result.get('nodes', []))}, Edges: {len(result.get('edges', []))}\n\n*Analysis complete.*"
                )
                self.notification_service.post_comment(repo_full_name, pr_number, result_comment)

            return result
        except Exception as e:
            log.error(f"Error analyzing PR: {e}")
            error_comment = f"## 🔗 ChAIn Reaction Analysis Error\n\n{str(e)}\n\n*Analysis failed.*"
            self.notification_service.post_comment(repo_full_name, pr_number, error_comment)

if __name__ == "__main__":
    pr_service = PullRequestService()
    # Example usage
    repo = "PrernaSharma23/ChAIn-Reaction"
    pr_no = 1
    response = pr_service.analyze_pr(repo, pr_no)
    print(response)