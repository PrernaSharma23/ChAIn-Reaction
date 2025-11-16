import os
from typing import List, Dict, Tuple

from src.extractor.java.java_extractor import JavaExtractor
from src.extractor.python.python_extractor import PythonExtractor


class ExtractorRouter:
    """
    Detects languages and delegates to correct extractor modules.
    """

    def __init__(self):
        self.extractors = [
            JavaExtractor(),
            PythonExtractor(),
        ]

    def extract_repo(self, repo_id: str, repo_path: str, repo_name: str) -> Tuple[List[Dict], List[Tuple]]:
        all_entities = []
        all_edges = []

        for ext in self.extractors:
            files = ext.detect_files(repo_path)
            print(f"[DEBUG] Extractor={ext.__class__.__name__}, files={files}")
            if not files:
                continue

            entities, edges = ext.extract(repo_id, repo_path, repo_name)
            all_entities.extend(entities)
            all_edges.extend(edges)

        # Ensure repo node exists
        all_entities.append({
            "uid": f"{repo_name}::repo",
            "repo_id": repo_id,
            "repo_name": repo_name,
            "kind": "repo",
            "name": repo_name,
            "language": "",
            "path": "",
            "meta": "{}",
        })

        return all_entities, all_edges
