import os
from tree_sitter_languages import get_parser
from src.util.logger import log
import datetime
import json
SUPPORTED_EXT = {
    ".py": "python",
    ".java": "java",
}

class TreeSitterExtractor:

    def __init__(self, languages=None):
        self.languages = languages or ["python", "java"]
        self.parsers = {}
        for lang in self.languages:
            try:
                self.parsers[lang] = get_parser(lang)
            except Exception as e:
                log.error(f"Failed to load parser for {lang}: {e}")

    # ------------------------------------------------------------------------
    # Language detector
    # ------------------------------------------------------------------------
    def get_language(self, filename):
        _, ext = os.path.splitext(filename)
        lang = SUPPORTED_EXT.get(ext)
        return lang if lang in self.parsers else None

    def extract_from_string(self, code: str, file_path: str, language: str):
         return self._extract_from_code(code, file_path, language)

    def extract_from_file(self, file_path: str, language: str):
        try:
            source = open(file_path, "r", encoding="utf-8").read()
        except:
            log.error(f"Could not read file: {file_path}")
            return []

        return self._extract_from_code(source, file_path, language)

    def _extract_from_code(self, code: str, file_path: str, language: str):
        try:
            source = open(file_path, "r", encoding="utf-8").read()
        except:
            log.error(f"Could not read file: {file_path}")
            return []

        parser = self.parsers[language]
        tree = parser.parse(source.encode("utf8"))
        root = tree.root_node
        symbols = []

        def get_text(node):
            try:
                return source[node.start_byte:node.end_byte]
            except:
                return ""

        # --------------------------------------------------------------------
        # Extract semantic children (common for both Python and Java)
        # --------------------------------------------------------------------
        def extract_semantic_children(node):
            semantic_types = {
                "class_definition": "Class",
                "class_declaration": "Class",
                "function_definition": "Function",
                "method_declaration": "Method",
                "import_statement": "Import",
                "import_declaration": "Import",
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

            for child in node.children:
                visit(child)

            return children

        # --------------------------------------------------------------------
        # Add symbol (common format)
        # --------------------------------------------------------------------
        def add_symbol(name, type_, node, parent_name=None):
            symbols.append({
                "name": name,
                "type": type_,
                "language": language,
                "parent": parent_name,
                "file": file_path,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "ast_type": node.type,
                "children": extract_semantic_children(node),
                "imports": [],
                "extends": []
            })

        # --------------------------------------------------------------------
        # AST traversal
        # --------------------------------------------------------------------
        def traverse(node, parent_name=None):
            t = node.type

            # Python
            if language == "python":
                if t == "class_definition":
                    id_node = next((c for c in node.children if c.type == "identifier"), None)
                    class_name = get_text(id_node).strip() if id_node else "<anonymous_class>"
                    add_symbol(class_name, "Class", node, parent_name)
                    parent_name = class_name

                elif t == "function_definition":
                    id_node = next((c for c in node.children if c.type == "identifier"), None)
                    func_name = get_text(id_node).strip() if id_node else "<anonymous_function>"
                    add_symbol(func_name, "Function", node, parent_name)

                elif t == "import_statement":
                    imp_text = get_text(node).strip()
                    if symbols:
                        symbols[-1]["imports"].append(imp_text)

                elif t == "import_from":
                    imp_text = get_text(node).strip()
                    if symbols:
                        symbols[-1]["imports"].append(imp_text)

                elif t == "argument_list":
                    # base classes: class A(B, C)
                    if parent_name and "(" in get_text(node):
                        bases = get_text(node)[1:-1].split(",")
                        for b in bases:
                            base = b.strip()
                            if base:
                                symbols[-1]["extends"].append(base)

            # Java
            elif language == "java":
                if t == "class_declaration":
                    id_node = next((c for c in node.children if c.type == "identifier"), None)
                    class_name = get_text(id_node).strip() if id_node else "<anonymous_class>"
                    add_symbol(class_name, "Class", node, parent_name)
                    parent_name = class_name

                elif t == "method_declaration":
                    id_node = next((c for c in node.children if c.type == "identifier"), None)
                    method_name = get_text(id_node).strip() if id_node else "<anonymous_method>"
                    add_symbol(method_name, "Method", node, parent_name)

                elif t == "import_declaration":
                    imp_text = get_text(node).strip()
                    if symbols:
                        symbols[-1]["imports"].append(imp_text)

                elif t in ("extends_interfaces", "superclass"):
                    ext_text = get_text(node).strip()
                    if symbols:
                        symbols[-1]["extends"].append(ext_text)

            # Continue recursion
            for child in node.children:
                traverse(child, parent_name)

        traverse(root)
        return symbols


    # ----------------------------------------------------------------------
    # 3. Convert symbols → Graph Nodes
    # ----------------------------------------------------------------------
    def convert_symbols_to_nodes(self, repo_name: str, rel_path: str, file_result):
        nodes = []
        now = datetime.datetime.utcnow().isoformat() + "Z"

        for entry in file_result["symbols"]:
            uid = f"{repo_name}:{rel_path}:{entry['type'].lower()}:{entry['name']}"

            node = {
                "uid": uid,
                "repo": repo_name,
                "kind": entry["type"].lower(),
                "name": entry["name"],
                "language": file_result["language"],
                "path": rel_path,
                "meta": json.dumps(entry["meta"]),
                "created_at": now
            }
            nodes.append(node)

        return nodes

    # ----------------------------------------------------------------------
    # 4. Build edges from symbols
    # ----------------------------------------------------------------------
    def derive_edges_from_symbols(self, repo_name: str, rel_path: str, file_result):
        edges = []

        # contains edges: file → class, class → method
        for s in file_result["symbols"]:
            if s["type"] == "Class":
                c_uid = f"{repo_name}:{rel_path}:class:{s['name']}"
                f_uid = f"{repo_name}:{rel_path}:file:{os.path.basename(rel_path)}"
                edges.append([f_uid, c_uid, "contains"])

            if s["type"] == "Method":
                m_uid = f"{repo_name}:{rel_path}:method:{s['name']}"
                c_uid = f"{repo_name}:{rel_path}:class:{s['parent']}"
                edges.append([c_uid, m_uid, "contains"])

            if s["type"] == "Extends":
                child = s["parent"]
                parent = s["name"].replace("extends", "").strip()

                c_uid = f"{repo_name}:{rel_path}:class:{child}"
                p_uid = f"{repo_name}:{rel_path}:class:{parent}"
                edges.append([c_uid, p_uid, "extends"])

        return edges

    # ----------------------------------------------------------------------
    # 5. Extract from a repo path
    # ----------------------------------------------------------------------
    def extract_from_repo(self, repo_name: str, repo_path: str):
        nodes = []
        edges = []

        for root, _, files in os.walk(repo_path):
            for fname in files:
                lang = self.get_language(fname)
                if not lang:
                    continue

                file_path = os.path.join(root, fname)
                rel_path = os.path.relpath(file_path, repo_path)

                file_res = self.extract_from_file(file_path, lang)
                if not file_res:
                    continue

                nodes += self.convert_symbols_to_nodes(repo_name, rel_path, file_res)
                edges += self.derive_edges_from_symbols(repo_name, rel_path, file_res)

        return {"nodes": nodes, "edges": edges}
