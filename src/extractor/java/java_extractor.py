# src/extractor/java/java_extractor.py
import os
from tree_sitter_languages import get_parser
from src.extractor.base_extractor import BaseExtractor
from src.extractor.java.java_ast import JavaAST
from src.util.debug import dbg

class JavaExtractor(BaseExtractor):
    EXTENSIONS = [".java"]

    def __init__(self):
        dbg("JavaExtractor: initializing parser for java")
        self.parser = get_parser("java")

    def extract(self, repo_id: str, repo_path: str, repo_name: str):
        dbg("JavaExtractor.extract repo_path=", repo_path)

        entities = []
        edges = []

        java_files = self.detect_files(repo_path)
        dbg("JavaExtractor: detected java files:", java_files)

        for path in java_files:
            rel = os.path.relpath(path, repo_path)

            with open(path, "r", encoding="utf-8") as f:
                src = f.read()

            dbg(f"Parsing file {rel}, len={len(src)}")

            tree = self.parser.parse(src.encode("utf-8"))
            root = tree.root_node
            dbg("Root node type:", root.type)

            ast = JavaAST(repo_name, rel, src)
            file_nodes, file_edges = ast.walk(root)

            dbg(f"File {rel}: extracted {len(file_nodes)} nodes, {len(file_edges)} edges")

            entities.extend(file_nodes)
            edges.extend(file_edges)

        dbg("JavaExtractor: FINAL totals:", len(entities), "nodes", len(edges), "edges")
        return entities, edges
