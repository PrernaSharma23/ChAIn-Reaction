from src.processor.repo_processor import RepoProcessor
from src.repository.neo4j_repository import Neo4jRepository

from src.util.logger import log

class ProjectService:
    def __init__(self):
        self.processor = RepoProcessor()
        self.neo_repo = Neo4jRepository()
        self._nodes = []
        self._edges = []

    def process_repository(self, repo_url: str):
        log.info(f"Processing repository: {repo_url}")
        data = self.processor.process(repo_url)
        self._nodes = data.get("nodes", [])
        self._edges = data.get("edges", [])
        return {
            "message": "extraction_complete",
            "nodes": self._nodes
            #"edges_count": len(self._edges),
        }

    def get_all_nodes(self):
        return self.neo_repo.get_all_nodes()

    def get_all_edges(self):
        return self.neo_repo.get_all_edges()

    def clear_graph(self):
        self.neo_repo.clear_all()