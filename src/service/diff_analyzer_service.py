from src.processor.tree_sitter_extractor import TreeSitterExtractor
from src.util.logger import log


class DiffAnalyzerService:
    def __init__(self, ):
        self.extractor = TreeSitterExtractor()

    def analyze_files(self, files_content: dict) -> dict:
        try:
            all_nodes, all_edges = [], []

            for file_path, content in files_content.items():
                lang = self.extractor.get_language(file_path)
                if not lang:
                    continue

                symbols = self.extractor.extract_from_string(content, file_path, lang)
                file_result = {"symbols": symbols, "language": lang}

                nodes = self.extractor.convert_symbols_to_nodes("repo", file_path, file_result)
                edges = self.extractor.derive_edges_from_symbols("repo", file_path, file_result)
                all_nodes += nodes
                all_edges += edges

            return {"nodes": all_nodes, "edges": all_edges}
        except Exception as e:
            log.error(f"DiffAnalyzerService.analyze_files error: {e}")
            return {"error": str(e)}
