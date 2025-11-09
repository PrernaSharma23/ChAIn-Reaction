import tempfile
import os
import git
from tree_sitter_languages import get_parser
from src.util.logger import log


class RepoProcessor:
    def __init__(self):
        """
        Initialize Tree-sitter parsers for Java and Python.
        """
        self.parsers = {
            "java": get_parser("java"),
            "python": get_parser("python")
        }
        log.info("Initialized Tree-sitter parsers for Java and Python")

    def process(self, repo_url: str):
        """
        Clone the repo and extract class and method/function names
        from both Java and Python files using Tree-sitter.
        """
        tmp_dir = tempfile.mkdtemp()
        log.info(f"Cloning repo from {repo_url} into {tmp_dir}")
        git.Repo.clone_from(repo_url, tmp_dir)

        graph_data = {"nodes": []}

        for root, _, files in os.walk(tmp_dir):
            for file in files:
                file_path = os.path.join(root, file)

                if file.endswith(".java"):
                    lang = "java"
                elif file.endswith(".py"):
                    lang = "python"
                else:
                    continue  # skip other file types

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        source_code = f.read()
                except Exception as e:
                    log.error(f"Error reading {file_path}: {e}")
                    continue

                parser = self.parsers[lang]
                tree = parser.parse(bytes(source_code, "utf8"))
                root_node = tree.root_node
                source_bytes = bytes(source_code, "utf8")

                def get_text(node):
                    return source_bytes[node.start_byte:node.end_byte].decode("utf8")

                def traverse(node, parent_class=None):
                    # --- Java-specific-handling ---
                    if lang == "java" and node.type == "class_declaration":
                        name_node = next((c for c in node.children if c.type == "identifier"), None)
                        class_name = get_text(name_node) if name_node else "<anonymous_class>"
                        graph_data["nodes"].append({
                            "type": "Class",
                            "language": "Java",
                            "name": class_name,
                            "file": os.path.relpath(file_path, tmp_dir)
                        })
                        parent_class = class_name

                    elif lang == "java" and node.type == "method_declaration":
                        name_node = next((c for c in node.children if c.type == "identifier"), None)
                        method_name = get_text(name_node) if name_node else "<anonymous_method>"
                        graph_data["nodes"].append({
                            "type": "Method",
                            "language": "Java",
                            "name": method_name,
                            "class": parent_class,
                            "file": os.path.relpath(file_path, tmp_dir)
                        })

                    # --- Python-specific-handling ---
                    elif lang == "python" and node.type == "class_definition":
                        name_node = next((c for c in node.children if c.type == "identifier"), None)
                        class_name = get_text(name_node) if name_node else "<anonymous_class>"
                        graph_data["nodes"].append({
                            "type": "Class",
                            "language": "Python",
                            "name": class_name,
                            "file": os.path.relpath(file_path, tmp_dir)
                        })
                        parent_class = class_name

                    elif lang == "python" and node.type == "function_definition":
                        name_node = next((c for c in node.children if c.type == "identifier"), None)
                        func_name = get_text(name_node) if name_node else "<anonymous_function>"
                        graph_data["nodes"].append({
                            "type": "Function",
                            "language": "Python",
                            "name": func_name,
                            "class": parent_class,
                            "file": os.path.relpath(file_path, tmp_dir)
                        })

                    # recurse
                    for child in node.children:
                        traverse(child, parent_class)

                traverse(root_node)

        log.info(f"Processed repo {repo_url} → Found {len(graph_data['nodes'])} symbols")
        return graph_data
