import os
from typing import List, Dict, Tuple

class BaseExtractor:
    """
    Every language extractor must implement:
      - detect_files(repo_path)
      - extract(repo_id, repo_path, repo_name)
    """

    EXTENSIONS = []  # override

    def detect_files(self, repo_path: str) -> List[str]:
        matches = []
        for root, _, files in os.walk(repo_path):
            for f in files:
                if any(f.endswith(ext) for ext in self.EXTENSIONS):
                    matches.append(os.path.join(root, f))
        return matches

    def extract(self, repo_id: str, repo_path: str, repo_name: str) -> Tuple[List[Dict], List[Tuple]]:
        raise NotImplementedError("extract() must be implemented by subclass")