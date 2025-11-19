import os
import shutil
import tempfile
import uuid

import git
from src.processor.repo_processor import RepoProcessor
from src.processor.tree_sitter_extractor import TreeSitterExtractor
from src.util.logger import log


class DiffAnalyzerService:
    def __init__(self, ):
        self.repo_processor = RepoProcessor()

    def make_tmp_dir(self, repo_name: str) -> str:
        tmp_dir = f"./tmp/{repo_name}-{uuid.uuid4().hex[:8]}"
        os.makedirs("./tmp", exist_ok=True)

        if os.path.exists(tmp_dir):
            try:
                shutil.rmtree(tmp_dir)
            except Exception as e:
                git.rmtree(tmp_dir)

        os.makedirs(tmp_dir, exist_ok=True)
        return tmp_dir

    def analyze_files(self, pr_number: int, files_content: dict, repo: dict) -> dict:
        """
        files_content: { "rel/path/to/file.py": "file contents", ... }
        repo: { "id": "<repo_id>", "name": "<repo_name>", "repo_url": "<git clone url>" }
        """
        repo_id = repo["id"]
        repo_name = repo["name"]
        temp_dir = self.make_tmp_dir(repo_name)
        try:
            for rel_path, content in (files_content or {}).items():
                    abs_path = os.path.join(temp_dir, rel_path.lstrip("/\\"))
                    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                    with open(abs_path, "w", encoding="utf-8") as f:
                        f.write(content)

            nodes, edges = self.repo_processor.process(repo_id, temp_dir, repo_name)
            return {"nodes": [n.to_dict() for n in nodes], "edges": [e.to_dict() for e in edges]}
        except Exception as e:
            log.error(f"DiffAnalyzerService.analyze_files error: {e}")
            return {"error": str(e)}
        finally:
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    log.warning(f"Could not remove temp dir {temp_dir}: {e}")
