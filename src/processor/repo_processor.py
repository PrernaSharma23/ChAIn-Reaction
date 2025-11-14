import tempfile
import os
import git
from tree_sitter import Language, Parser
from tree_sitter_languages import get_language, get_parser

from src.util.logger import log

github_token = os.getenv("GITHUB_TOKEN")

class RepoProcessor:
    def __init__(self):
        """
        Initialize Tree-sitter parser for Java.
        For multi-language support, you can load more parsers dynamically.
        """
        self.parser = get_parser("java")
        log.info("Initialized Tree-sitter parser for Java")

    def clone_repo(self, repo_name:str, repo_url: str):
        tmp_dir = tempfile.mkdtemp(dir="./tmp", prefix=repo_name+"_")
        log.info(f"Cloning repo from {repo_url} into {tmp_dir}")
        
        if github_token:
            repo_url_with_auth = repo_url.replace("https://", f"https://{github_token}@")
        git.Repo.clone_from(repo_url_with_auth, tmp_dir)
        return tmp_dir
    
    def process(self, repo_path: str):
        graph_data = {"nodes": [], "edges": []}
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith(".java"):
                    graph_data["nodes"].append({"type": "File", "name": file})
                    # (Placeholder — later extract functions/classes/params)
        return graph_data
