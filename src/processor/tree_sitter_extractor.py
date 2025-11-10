# src/processor/tree_sitter_extractor.py

import tempfile
import os
import shutil
import git
from tree_sitter_languages import get_parser
from src.util.logger import log


SUPPORTED_EXT = {
    ".py": "python",
    ".java": "java",
}


class TreeSitterExtractor:
    """
    Clone a repo, iterate files, and extract rich symbol metadata
    using Tree-sitter parsers for Python and Java.
    """

    def __init__(self, languages=None):
        self.languages = languages or ["python", "java"]
        self.parsers = {}
        for lang in self.languages:
            try:
                self.parsers[lang] = get_parser(lang)
            except Exception as e:
                log.error("Failed to load parser for %s: %s", lang, e)
        log.info("TreeSitterExtractor initialized for languages: %s", list(self.parsers.keys()))

    def _get_language_for_file(self, filename):
        _, ext = os.path.splitext(filename)
        lang = SUPPORTED_EXT.get(ext)
        if lang and lang in self.parsers:
            return lang
        return None

    def extract_from_file(self, file_path: str, language: str):
        """
        Parse a single file and return rich symbol metadata for each node.
        """
        if language not in self.parsers:
            log.warning("No parser for language %s (file %s) - skipping", language, file_path)
            return []

        parser = self.parsers[language]

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
        except Exception as e:
            log.error("Could not read %s: %s", file_path, e)
            return []

        source_bytes = source.encode("utf8")

        try:
            tree = parser.parse(source_bytes)
        except Exception as e:
            log.error("Tree-sitter parse failed for %s: %s", file_path, e)
            return []

        root = tree.root_node
        symbols = []

        def get_text(node):
            try:
                return source_bytes[node.start_byte:node.end_byte].decode("utf8")
            except Exception:
                return ""

        def extract_semantic_children(node):
            semantic_types = {
                "class_definition": "Class",
                "class_declaration": "Class",
                "function_definition": "Function",
                "method_declaration": "Method",
                "import_statement": "Import",
                "import_declaration": "Import"
            }

            children = []

            def visit(n):
                if n.type in semantic_types:
                    children.append({
                        "name": get_text(n).split("(")[0].strip()[:100],
                        "type": semantic_types[n.type],
                        "start_line": n.start_point[0] + 1,
                        "end_line": n.end_point[0] + 1,
                    })
                for c in n.children:
                    visit(c)

            # recursively explore everything inside this node
            for child in node.children:
                visit(child)

            return children

        def add_symbol(name, type_, node, parent_name=None):
            symbols.append({
                "name": name,
                "type": type_,
                "language": language.capitalize(),
                "parent": parent_name,
                "file": file_path,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "ast_type": node.type,
                "children": extract_semantic_children(node),
                #"text": get_text(node)[:500],
                # "calls": [],
                # "imports": [],
                # "extends": [],
                # "references": [],
            })

        def traverse(node, parent_name=None):
            if language == "python":
                if node.type == "class_definition":
                    name_node = next((c for c in node.children if c.type == "identifier"), None)
                    class_name = get_text(name_node) if name_node else "<anonymous_class>"
                    add_symbol(class_name, "Class", node, parent_name)
                    parent_name = class_name

                elif node.type == "function_definition":
                    name_node = next((c for c in node.children if c.type == "identifier"), None)
                    func_name = get_text(name_node) if name_node else "<anonymous_function>"
                    add_symbol(func_name, "Function", node, parent_name)

                elif node.type == "import_statement":
                    imp_text = get_text(node)
                    if symbols:
                        symbols[-1]["imports"].append(imp_text)

            elif language == "java":
                if node.type == "class_declaration":
                    name_node = next((c for c in node.children if c.type == "identifier"), None)
                    class_name = get_text(name_node) if name_node else "<anonymous_class>"
                    add_symbol(class_name, "Class", node, parent_name)
                    parent_name = class_name

                elif node.type == "method_declaration":
                    name_node = next((c for c in node.children if c.type == "identifier"), None)
                    method_name = get_text(name_node) if name_node else "<anonymous_method>"
                    add_symbol(method_name, "Method", node, parent_name)

                elif node.type == "import_declaration":
                    imp_text = get_text(node)
                    if symbols:
                        symbols[-1]["imports"].append(imp_text)

                elif node.type in ("extends_interfaces", "superclass"):
                    ext_text = get_text(node)
                    if symbols:
                        symbols[-1]["extends"].append(ext_text)

            for child in node.children:
                traverse(child, parent_name)

        traverse(root)
        return symbols

    def extract_from_repo(self, repo_url: str, commit_id=None):
        """
        Clone repo to a temp dir, extract all supported files, and return:
        {"nodes": [...], "edges": []}
        """
        tmp_dir = tempfile.mkdtemp(prefix="extractor_")
        log.info("Cloning %s into %s", repo_url, tmp_dir)

        try:
            repo = git.Repo.clone_from(repo_url, tmp_dir)
            commit_id = commit_id or repo.head.commit.hexsha
        except Exception as e:
            log.error("Git clone failed: %s", e)
            shutil.rmtree(tmp_dir, ignore_errors=True)
            raise

        nodes = []
        try:
            for root_dir, _, files in os.walk(tmp_dir):
                for fname in files:
                    file_path = os.path.join(root_dir, fname)
                    try:
                        if os.path.getsize(file_path) == 0:
                            continue
                    except Exception:
                        continue

                    lang = self._get_language_for_file(fname)
                    if not lang:
                        continue

                    try:
                        symbols = self.extract_from_file(file_path, lang)
                        rel_path = os.path.relpath(file_path, tmp_dir)
                        for s in symbols:
                            s["file"] = rel_path
                            s["repo_url"] = repo_url
                            s["commit_id"] = commit_id
                            nodes.append(s)
                    except Exception as e:
                        log.error("Failed to extract from %s: %s", file_path, e)
                        continue
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            log.info("Cleaned up temporary dir %s", tmp_dir)

        return {"nodes": nodes, "edges": []}
