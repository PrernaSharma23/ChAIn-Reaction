import os
from shutil import rmtree
from src.processor.repo_processor import RepoProcessor
from src.repository.neo4j_repository import Neo4jRepository
from src.util.logger import log

class ProjectService:
    def __init__(self):
        self.repo_processor = RepoProcessor()
        self.neo_repo = Neo4jRepository()

    def process_repository(self, repo_id: str, repo_name: str, repo_url: str, force_reclone: bool = False):

        repo_path = None
        log.info(f"Started processing for repository: {repo_url}")
        try:
            repo_path = self.repo_processor.clone_repo(repo_name, repo_url, force=force_reclone)

            nodes, edges = self.repo_processor.process(repo_id, repo_path, repo_name)
            log.info(f"Extracted {len(nodes)} nodes & {len(edges)} edges. Ingesting...")

            self.neo_repo.store_graph(nodes, edges)

            return {
                "message": "Repository processed and graph created",
                "nodes": len(nodes),
                "edges": len(edges)
            }

        except Exception as e:
            log.error(f"Error processing repository {repo_url}: {e}")
            raise

        finally:
            if repo_path and os.path.exists(repo_path):
                try:
                    rmtree(repo_path)
                    log.info(f"Removed temporary repo at {repo_path}")
                except Exception as ex:
                    log.warning(f"Could not remove {repo_path}: {ex}")

    def get_all_nodes(self):
        return self.neo_repo.get_all_nodes()

    def get_all_edges(self):
        return self.neo_repo.get_all_edges()

    def clear_graph(self):
        return self.neo_repo.clear_all()

    def get_edges_between_repos(self, repo_a: str, repo_b: str):
        """
        wrapper to fetch cross-repo dependencies both directions.
        """
        return self.neo_repo.get_edges_between_repos(repo_a, repo_b)
