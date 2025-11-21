import tempfile
import os
import shutil
import git
from typing import List, Tuple
from src.util.logger import log
from src.model.graph_model import GraphNode, GraphEdge
from src.extractor.extract_repo import ExtractorRouter


github_token = os.getenv("GITHUB_TOKEN")


class RepoProcessor:

    def __init__(self):
        self.router = ExtractorRouter()
        log.info("Initialized Extractor Router")

    def clone_repo(self, repo_name: str, repo_url: str):
        tmp_dir = f"./tmp/{repo_name}"
        os.makedirs("./tmp", exist_ok=True)

        if os.path.exists(tmp_dir):
            git.rmtree(tmp_dir)

        log.info(f"Cloning repo from {repo_url} into {tmp_dir}")

        if github_token:
            repo_url = repo_url.replace("https://", f"https://{github_token}@")

        git.Repo.clone_from(repo_url, tmp_dir)
        return tmp_dir

    def process(self, repo_id: str, repo_path: str, repo_name: str) -> Tuple[List[GraphNode], List[GraphEdge]]:
        entities_raw, edges_raw = self.router.extract_repo(repo_id, repo_path, repo_name)

        node_objs: List[GraphNode] = []
        edge_objs: List[GraphEdge] = []

        for e in entities_raw:
            try:
                node_objs.append(GraphNode.from_dict(e))
            except Exception as ex:
                log.error(f"[WARN] Invalid entity skipped: {ex}")

        for e in edges_raw:
            try:
                if isinstance(e, dict):
                    src = e["src"]
                    dst = e["dst"]
                    t = e["type"]
                else:
                    src, dst, t = e
                edge_objs.append(GraphEdge(src=src, dst=dst, type=t))
            except Exception as ex:
                log.error(f"[WARN] Invalid edge skipped: {ex}")

        return node_objs, edge_objs