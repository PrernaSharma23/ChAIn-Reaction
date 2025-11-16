import os
from tree_sitter import Node
from tree_sitter_languages import get_language

PY_LANG = get_language("python")


class PythonAST:
    LANG = PY_LANG

    def __init__(self, repo_name, rel_path):
        self.repo = repo_name
        self.path = rel_path

    # ---------- GENERIC DFS WALK ----------
    def _walk(self, node: Node):
        yield node
        for child in node.children:
            yield from self._walk(child)

    # ---------- NAME EXTRACTION ----------
    def _extract_identifier(self, src_bytes, node: Node):
        for child in node.children:
            if child.type == "identifier":
                return src_bytes[child.start_byte:child.end_byte].decode("utf8")
        return "unknown"

    # ---------- MAIN WALK ----------
    def walk(self, root: Node, src: str):
        src_bytes = src.encode("utf8")

        entities = []
        edges = []

        file_uid = f"{self.repo}:{self.path}"

        # ------------------------ FILE NODE ------------------------
        entities.append({
            "uid": file_uid,
            "repo": self.repo,
            "kind": "file",
            "name": os.path.basename(self.path),
            "language": "python",
            "path": self.path,
            "meta": "{}",
        })

        # ------------------------ WALK AST -------------------------
        for node in self._walk(root):

            # -------- class declarations --------
            if node.type == "class_definition":
                name = self._extract_identifier(src_bytes, node)
                uid = f"{file_uid}:class:{name}"

                entities.append({
                    "uid": uid,
                    "repo": self.repo,
                    "kind": "class",
                    "name": name,
                    "language": "python",
                    "path": self.path,
                    "meta": "{}",
                })

                edges.append((file_uid, uid, "CONTAINS"))

            # -------- function declarations --------
            elif node.type == "function_definition":
                name = self._extract_identifier(src_bytes, node)
                uid = f"{file_uid}:method:{name}"

                entities.append({
                    "uid": uid,
                    "repo": self.repo,
                    "kind": "method",
                    "name": name,
                    "language": "python",
                    "path": self.path,
                    "meta": "{}",
                })

                edges.append((file_uid, uid, "CONTAINS"))

        return entities, edges