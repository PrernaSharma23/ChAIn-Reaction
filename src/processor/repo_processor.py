import tempfile
import os
import git
from src.util.logger import log
from typing import Tuple, List
from src.model.graph_model import GraphNode, GraphEdge
from src.extractor.extract_repo import ExtractorRouter

github_token = os.getenv("GITHUB_TOKEN")

class RepoProcessor:
    def __init__(self):
        """
        Initialize Tree-sitter parser for Java.
        For multi-language support, you can load more parsers dynamically.
        """
        self.router = ExtractorRouter()
        log.info("Initialized Extractor Router")

    def clone_repo(self, repo_name:str, repo_url: str):
        tmp_dir = tempfile.mkdtemp(dir="./tmp", prefix=repo_name+"_")
        log.info(f"Cloning repo from {repo_url} into {tmp_dir}")
        
        if github_token:
            repo_url_with_auth = repo_url.replace("https://", f"https://{github_token}@")
        git.Repo.clone_from(repo_url_with_auth, tmp_dir)
        return tmp_dir

    def process(self, repo_path: str, repo_name: str) -> Tuple[List[GraphNode], List[GraphEdge]]:
        """
        Detect languages in repo and call matching extractors through ExtractorRouter.
        """
        entities_raw, edges_raw = self.router.extract_repo(repo_path, repo_name)

        node_objs: List[GraphNode] = []
        edge_objs: List[GraphEdge] = []

        for n in entities_raw:
            try:
                node_objs.append(GraphNode.from_dict(n))
            except Exception:
                continue

        for e in edges_raw:
            try:
                if isinstance(e, dict):
                    src = e["src"]
                    dst = e["dst"]
                    t = e["type"]
                else:
                    src, dst, t = e
                edge_objs.append(GraphEdge(src=src, dst=dst, type=t))
            except Exception:
                continue

        return node_objs, edge_objs
