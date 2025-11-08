import os
import json
from tree_sitter import Language, Parser

from src.util.logger import log

# Load compiled language library
LANGUAGE_LIB_PATH = os.path.join(os.path.dirname(__file__), "build/my-languages.so")
Language.build_library(
    LANGUAGE_LIB_PATH,
    [
        "vendor/tree-sitter-python",
        "vendor/tree-sitter-java"
    ]
)

PY_LANGUAGE = Language(LANGUAGE_LIB_PATH, "python")
JAVA_LANGUAGE = Language(LANGUAGE_LIB_PATH, "java")

def extract_symbols(file_path: str, language: str):
    parser = Parser()
    if language == "python":
        parser.set_language(PY_LANGUAGE)
    elif language == "java":
        parser.set_language(JAVA_LANGUAGE)
    else:
        raise ValueError(f"Unsupported language: {language}")

    with open(file_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    tree = parser.parse(bytes(source_code, "utf8"))
    root = tree.root_node

    symbols = []

    def traverse(node, parent_name=None):
        if node.type in ("function_definition", "method_declaration"):
            name_node = node.child_by_field_name("name")
            if name_node:
                func_name = name_node.text.decode()
                symbols.append({
                    "name": func_name,
                    "type": "function",
                    "parent": parent_name,
                    "start": node.start_point,
                    "end": node.end_point,
                })
        elif node.type in ("class_definition", "class_declaration"):
            name_node = node.child_by_field_name("name")
            if name_node:
                class_name = name_node.text.decode()
                symbols.append({
                    "name": class_name,
                    "type": "class",
                    "start": node.start_point,
                    "end": node.end_point,
                })
                parent_name = class_name

        for child in node.children:
            traverse(child, parent_name)

    traverse(root)
    return symbols

if __name__ == "__main__":
    file_path = "example.py"
    symbols = extract_symbols(file_path, "python")
    print(json.dumps(symbols, indent=2))