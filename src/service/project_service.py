import os
from git import rmtree
from src.processor.repo_processor import RepoProcessor
from src.processor.tree_sitter_extractor import TreeSitterExtractor
from src.repository.neo4j_repository import Neo4jRepository

from src.util.logger import log

class ProjectService:
    def __init__(self):
        self.repo_processor = RepoProcessor()
        self.tree_sitter_extractor = TreeSitterExtractor()
        self.neo_repo = Neo4jRepository()

    def process_repository(self, repo_name: str, repo_url: str):
        """
        Clone and process repo, generate dependency graph using Tree-sitter,
        and store results in Neo4j.
        """
        repo_path = ""
        log.info(f"Started async processing for repository: {repo_url}")
        try : 
            repo_path = self.repo_processor.clone_repo(repo_name, repo_url)
            graph_data = self.tree_sitter_extractor.extract_from_repo(repo_name, repo_path)
            # self.neo_repo.store_graph(graph_data)
            return {"message": "Repository processed and graph created"}
        except Exception as e:
            log.error(f"Error processing repository: {e}")
            raise e
        finally:
            if repo_path and os.path.exists(repo_path):
                log.info(f"Cleaning up temporary repo at {repo_path}")
                rmtree(repo_path)

    def get_all_nodes(self):
        return self.neo_repo.get_all_nodes()

    def get_all_edges(self):
        return self.neo_repo.get_all_edges()

    def clear_graph(self):
        self.neo_repo.clear_all()