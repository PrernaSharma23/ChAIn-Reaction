import os
from src.util.logger import log

class DiffAnalyzerService:
    def __init__(self):
        from src.extractor.java.java_extractor import JavaExtractor
        from src.extractor.python.python_extractor import PythonExtractor

        self.extractors = {
            ".java": JavaExtractor(),
            ".py": PythonExtractor(),
        }

    def analyze_files(self, repo_full_name: str, files_content: dict) -> dict:
        try:
            all_nodes, all_edges = [], []

            for file_path, content in files_content.items():
                if not content:
                    continue

                ext = os.path.splitext(file_path)[1]

                extractor = self.extractors.get(ext)
                if not extractor:
                    continue  

                if ext == ".java":
                    from src.extractor.java.java_ast import JavaAST
                    ast = JavaAST("PR", repo_full_name, file_path, content)

                    tree = extractor.parser.parse(content.encode("utf-8"))
                    nodes, edges = ast.walk(tree.root_node)

                elif ext == ".py":
                    from src.extractor.python.python_ast import PythonAST
                    ast = PythonAST("PR", repo_full_name, file_path, content)

                    tree = extractor.parser.parse(content.encode("utf-8"))
                    nodes, edges = ast.walk(tree.root_node)

                all_nodes.extend(nodes)
                all_edges.extend(edges)

            return {"nodes": all_nodes, "edges": all_edges}

        except Exception as e:
            log.error(f"DiffAnalyzerService.analyze_files error: {e}")
            return {"error": str(e)}
