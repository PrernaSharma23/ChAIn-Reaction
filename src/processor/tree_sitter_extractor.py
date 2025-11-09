import os
import json
from tree_sitter_languages import get_parser
from src.util.logger import log


# Initialize parsers for Java and Python
PARSERS = {
    "python": get_parser("python"),
    "java": get_parser("java"),
}


def extract_symbols(file_path: str, language: str):
    """
    Extracts class and method/function names from the given file
    using Tree-sitter for the specified language.
    """
    if language not in PARSERS:
        raise ValueError(f"Unsupported language: {language}")

    parser = PARSERS[language]

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
    except Exception as e:
        log.error(f"Error reading {file_path}: {e}")
        return []

    tree = parser.parse(bytes(source_code, "utf8"))
    root_node = tree.root_node
    source_bytes = bytes(source_code, "utf8")

    symbols = []

    def get_text(node):
        return source_bytes[node.start_byte:node.end_byte].decode("utf8")

    def traverse(node, parent_name=None):
        # --- Python: class and function definitions ---
        if language == "python":
            if node.type == "class_definition":
                name_node = next((c for c in node.children if c.type == "identifier"), None)
                class_name = get_text(name_node) if name_node else "<anonymous_class>"
                symbols.append({
                    "name": class_name,
                    "type": "Class",
                    "language": "Python",
                    "file": file_path,
                })
                parent_name = class_name

            elif node.type == "function_definition":
                name_node = next((c for c in node.children if c.type == "identifier"), None)
                func_name = get_text(name_node) if name_node else "<anonymous_function>"
                symbols.append({
                    "name": func_name,
                    "type": "Function",
                    "language": "Python",
                    "parent": parent_name,
                    "file": file_path,
                })

        # --- Java: class and method declarations ---
        elif language == "java":
            if node.type == "class_declaration":
                name_node = next((c for c in node.children if c.type == "identifier"), None)
                class_name = get_text(name_node) if name_node else "<anonymous_class>"
                symbols.append({
                    "name": class_name,
                    "type": "Class",
                    "language": "Java",
                    "file": file_path,
                })
                parent_name = class_name

            elif node.type == "method_declaration":
                name_node = next((c for c in node.children if c.type == "identifier"), None)
                method_name = get_text(name_node) if name_node else "<anonymous_method>"
                symbols.append({
                    "name": method_name,
                    "type": "Method",
                    "language": "Java",
                    "parent": parent_name,
                    "file": file_path,
                })

        # Recurse
        for child in node.children:
            traverse(child, parent_name)

    traverse(root_node)
    return symbols


if __name__ == "__main__":
    # quick test mode
    sample_file = input("Enter path to a .py or .java file to test: ").strip()
    if sample_file.endswith(".py"):
        lang = "python"
    elif sample_file.endswith(".java"):
        lang = "java"
    else:
        print("Unsupported file type.")
        exit()

    result = extract_symbols(sample_file, lang)
    print(json.dumps(result, indent=2))
