"""
Takes symbols.jsonl and creates basic nodes into Neo4j (File and Function/Class nodes and 'contains' edges).
Requires Neo4j 5 and neo4j python driver.
"""
from neo4j import GraphDatabase
import json

from src.util.logger import log

class Neo4jIngestor:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def ingest_symbols(self, file_path, symbols):
        with self.driver.session() as session:
            session.execute_write(self._create_file_node, file_path)
            for sym in symbols:
                session.execute_write(self._create_symbol_node, file_path, sym)

    @staticmethod
    def _create_file_node(tx, file_path):
        tx.run("MERGE (f:File {path: $path})", path=file_path)

    @staticmethod
    def _create_symbol_node(tx, file_path, sym):
        tx.run(
            """
            MERGE (s:Symbol {name: $name, type: $type})
            WITH s
            MATCH (f:File {path: $file_path})
            MERGE (f)-[:CONTAINS]->(s)
            """,
            name=sym["name"], type=sym["type"], file_path=file_path
        )

if __name__ == "__main__":
    with open("sample_symbols.jsonl", "r") as f:
        data = [json.loads(line) for line in f]
    ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
    for item in data:
        ingestor.ingest_symbols(item["file"], item["symbols"])
    ingestor.close()
