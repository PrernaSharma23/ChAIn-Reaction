import os
from datetime import datetime
from tree_sitter import Language
from tree_sitter_languages import get_language

PY_LANG = get_language("python")


class PythonAST:
    LANG = PY_LANG

    def __init__(self, repo, path):
        self.repo = repo
        self.path = path

    def walk(self, node, src):
        nodes = []
        edges = []

        file_uid = f"{self.repo}:{self.path}"
        nodes.append({
            "uid": file_uid,
            "repo": self.repo,
            "kind": "file",
            "name": os.path.basename(self.path),
            "language": "python",
            "path": self.path,
            "meta": "{}",
        })

        for child in node.children:
            if child.type == "function_definition":
                fn_name = self._get_name(src, child)
                fn_uid = f"{file_uid}:{fn_name}"
                nodes.append({
                    "uid": fn_uid,
                    "repo": self.repo,
                    "kind": "function",
                    "name": fn_name,
                    "language": "python",
                    "path": self.path,
                    "meta": "{}",
                })
                edges.append((file_uid, fn_uid, "CONTAINS"))

        return nodes, edges

    def _get_name(self, src, node):
        text = src[node.start_byte:node.end_byte]
        parts = text.split()
        return parts[1].split("(")[0] if len(parts) > 1 else "unknown"
