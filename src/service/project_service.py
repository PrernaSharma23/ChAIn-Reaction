from src.processor.repo_processor import RepoProcessor
from src.repository.neo4j_repository import Neo4jRepository

from src.util.logger import log

class ProjectService:
    def __init__(self):
        self.repo_processor = RepoProcessor()
        self.neo_repo = Neo4jRepository()

    def process_repository(self, repo_url: str):
        """
        TODO
        Clone and process repo, generate dependency graph using Tree-sitter,
        and store results in Neo4j.
        """
        graph_data = self.repo_processor.process(repo_url)
        # self.neo_repo.store_graph(graph_data)
        return {"message": "Repository processed and graph created"}

    def get_all_nodes(self):
        return self.neo_repo.get_all_nodes()

    def get_all_edges(self):
        return self.neo_repo.get_all_edges()

    def clear_graph(self):
        self.neo_repo.clear_all()
