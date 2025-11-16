import os
from tree_sitter_languages import get_language

JAVA_LANG = get_language("java")


class JavaAST:
    LANG = JAVA_LANG

    def __init__(self, repo_name, rel_path):
        self.repo = repo_name
        self.path = rel_path

    # ---------- GENERIC DFS WALK ----------
    def _walk(self, node):
        yield node
        for child in node.children:
            yield from self._walk(child)

    # ---------- NAME EXTRACTION ----------
    def _extract_identifier(self, src, node):
        """
        Extract simple identifier name from class/method declarations.
        Java grammar has patterns like:
            (class_declaration name: (identifier))
            (method_declaration name: (identifier))
        """
        for child in node.children:
            if child.type == "identifier":
                return src[child.start_byte:child.end_byte].decode("utf8")
        return "unknown"

    # ---------- MAIN WALK ----------
    def walk(self, root, src_str):
        src = src_str.encode("utf8") if isinstance(src_str, str) else src_str

        nodes = []
        edges = []

        file_uid = f"{self.repo}:{self.path}"

        # FILE node
        nodes.append({
            "uid": file_uid,
            "repo": self.repo,
            "kind": "file",
            "name": os.path.basename(self.path),
            "language": "java",
            "path": self.path,
            "meta": "{}",
        })

        # DFS over entire AST
        for node in self._walk(root):

            # ------------------ class ------------------
            if node.type == "class_declaration":
                class_name = self._extract_identifier(src, node)
                class_uid = f"{file_uid}:class:{class_name}"

                nodes.append({
                    "uid": class_uid,
                    "repo": self.repo,
                    "kind": "class",
                    "name": class_name,
                    "language": "java",
                    "path": self.path,
                    "meta": "{}",
                })
                edges.append((file_uid, class_uid, "CONTAINS"))

            # ------------------ methods ------------------
            elif node.type == "method_declaration":
                method_name = self._extract_identifier(src, node)
                method_uid = f"{file_uid}:method:{method_name}"

                nodes.append({
                    "uid": method_uid,
                    "repo": self.repo,
                    "kind": "method",
                    "name": method_name,
                    "language": "java",
                    "path": self.path,
                    "meta": "{}",
                })
                edges.append((file_uid, method_uid, "CONTAINS"))

        return nodes, edges