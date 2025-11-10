# src/extractor/repo_processor.py
from src.processor.tree_sitter_extractor import TreeSitterExtractor
from src.util.logger import log

class RepoProcessor:
    """
    Coordinates multiple extractors (Tree-sitter, AI analyzers, etc.)
    Currently only Tree-sitter, but designed for future extensions.
    """

    def __init__(self):
        self.tree_sitter_extractor = TreeSitterExtractor()

    def process(self, repo_url: str):
        log.info(f"RepoProcessor: Starting processing for {repo_url}")
        graph_data = self.tree_sitter_extractor.extract_from_repo(repo_url)
        return graph_data