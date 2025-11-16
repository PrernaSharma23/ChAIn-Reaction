import os
from tree_sitter import Parser
from src.extractor.base_extractor import BaseExtractor
from src.extractor.java.java_ast import JavaAST


class JavaExtractor(BaseExtractor):
    EXTENSIONS = [".java"]

    def __init__(self):
        self.parser = Parser()
        self.parser.set_language(JavaAST.LANG)

    def extract(self, repo_path: str, repo_name: str):
        entities = []
        edges = []

        files = self.detect_files(repo_path)
        for path in files:
            rel = os.path.relpath(path, repo_path)

            with open(path, "r") as f:
                src = f.read()

            tree = self.parser.parse(src.encode("utf8"))

            ast = JavaAST(repo_name, rel)
            file_nodes, file_edges = ast.walk(tree.root_node, src)

            entities.extend(file_nodes)
            edges.extend(file_edges)

        return entities, edges