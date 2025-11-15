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

    def analyze_diff(self, diff_content: str) -> dict:
        from tempfile import TemporaryDirectory
        from src.processor.tree_sitter_extractor import TreeSitterExtractor

        try:
            # --- STEP 1: Parse unified diff into files ------------
            files = {}
            current_file = None
            old_lines = []
            new_lines = []

            for line in diff_content.split("\n"):
                if line.startswith("diff --git"):
                    # save previous file
                    if current_file:
                        files[current_file] = {
                            "old": "\n".join(old_lines),
                            "new": "\n".join(new_lines),
                        }
                    # start new file
                    parts = line.split(" ")
                    if len(parts) >= 3:
                        current_file = parts[2][2:]  # remove a/
                    old_lines, new_lines = [], []

                elif line.startswith("--- "):
                    continue
                elif line.startswith("+++ "):
                    continue

                elif line.startswith("-") and not line.startswith("---"):
                    old_lines.append(line[1:])
                elif line.startswith("+") and not line.startswith("+++"):
                    new_lines.append(line[1:])
                else:
                    old_lines.append(line)
                    new_lines.append(line)

            if current_file:
                files[current_file] = {
                    "old": "\n".join(old_lines),
                    "new": "\n".join(new_lines),
                }

            # --- STEP 2: Extract AST for old and new versions -------
            extractor = TreeSitterExtractor()
            changed_nodes = {}

            with TemporaryDirectory() as tmpdir:
                for file_path, versions in files.items():
                    filepath_old = os.path.join(tmpdir, "old_" + file_path.replace("/", "_"))
                    filepath_new = os.path.join(tmpdir, "new_" + file_path.replace("/", "_"))

                    # write reconstructed versions
                    with open(filepath_old, "w", encoding="utf-8") as f:
                        f.write(versions["old"])
                    with open(filepath_new, "w", encoding="utf-8") as f:
                        f.write(versions["new"])

                    ext = os.path.splitext(file_path)[1]
                    lang = extractor._get_language_for_file("dummy" + ext)
                    if not lang:
                        continue

                    old_ast = extractor.extract_from_file(filepath_old, lang)
                    new_ast = extractor.extract_from_file(filepath_new, lang)

                    # --- STEP 3: Compare AST symbols -------------
                    added = [node for node in new_ast if node not in old_ast]
                    removed = [node for node in old_ast if node not in new_ast]

                    if added or removed:
                        changed_nodes[file_path] = {
                            "added": added,
                            "removed": removed
                        }

            return {
                "changed_files": len(changed_nodes),
                "details": changed_nodes,
            }

        except Exception as e:
            log.error(f"Error analyzing diff: {e}")
            return {"error": str(e)}

    def analyze_pr(self, repo_full_name: str, pr_number: int) -> dict:
        try : 
            log.info(f"Analyzing PR {repo_full_name}#{pr_number}")
            files = self.get_pr_diff_files(repo_full_name, pr_number)
            for f in files:
                print(f["filename"], f["status"], f["sha"])
                file_content = self.download_file(repo_full_name, f["sha"])
            #TODO: parse file content via AST and build delta graph
            result =""
            
            if result:
                result_comment = f"## 🔗 ChAIn Reaction Analysis Results\n\n{str(result)}\n\n*Analysis complete.*"
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