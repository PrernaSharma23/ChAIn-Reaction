# src/extractor/python/python_extractor.py
import os
from tree_sitter_languages import get_parser
from src.extractor.base_extractor import BaseExtractor
from src.extractor.python.python_ast import PythonAST

class PythonExtractor(BaseExtractor):
    EXTENSIONS = [".py"]

    def __init__(self):
        self.parser = get_parser("python")

    def extract(self, repo_id: str, repo_path: str, repo_name: str):
        entities = []
        edges = []

        py_files = self.detect_files(repo_path)
        for path in py_files:
            rel = os.path.relpath(path, repo_path)
            with open(path, "r", encoding="utf-8") as f:
                src = f.read()

            tree = self.parser.parse(src.encode("utf-8"))
            ast = PythonAST(repo_name, rel, src)

            file_nodes, file_edges = ast.walk(tree.root_node)
            entities.extend(file_nodes)
            edges.extend(file_edges)

        return entities, edges