
import tempfile
import os
from src.processor.tree_sitter_extractor import TreeSitterExtractor
from src.util.logger import log

github_token = os.getenv("GITHUB_TOKEN")

class RepoProcessor:
    """
    Coordinates multiple extractors (Tree-sitter, AI analyzers, etc.)
    Currently only Tree-sitter, but designed for future extensions.
    """

    def __init__(self):
        self.tree_sitter_extractor = TreeSitterExtractor()

    def clone_repo(self, repo_name:str, repo_url: str):
        tmp_dir = tempfile.mkdtemp(dir="./tmp", prefix=repo_name+"_")
        log.info(f"Cloning repo from {repo_url} into {tmp_dir}")
        
        if github_token:
            repo_url_with_auth = repo_url.replace("https://", f"https://{github_token}@")
        git.Repo.clone_from(repo_url_with_auth, tmp_dir)
        return tmp_dir
    
    # def process(self, repo_path: str):
    #     graph_data = {"nodes": [], "edges": []}
    #     for root, _, files in os.walk(repo_path):
    #         for file in files:
    #             if file.endswith(".java"):
    #                 graph_data["nodes"].append({"type": "File", "name": file})
    #                 # (Placeholder — later extract functions/classes/params)
    #     return graph_data
    def process(self, repo_url: str):
        log.info(f"RepoProcessor: Starting processing for {repo_url}")
        graph_data = self.tree_sitter_extractor.extract_from_repo(repo_url)
        return graph_data