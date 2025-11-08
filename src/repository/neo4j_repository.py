from neo4j import GraphDatabase

from src.util.logger import log

class Neo4jRepository:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def store_graph(self, graph_data):
        with self.driver.session() as session:
            for node in graph_data.get("nodes", []):
                session.run("CREATE (n:Node {name:$name, type:$type})", name=node["name"], type=node["type"])

            for edge in graph_data.get("edges", []):
                session.run("""
                    MATCH (a:Node {name:$src}), (b:Node {name:$dst})
                    CREATE (a)-[:DEPENDS_ON]->(b)
                """, src=edge["src"], dst=edge["dst"])

    def get_all_nodes(self):
        with self.driver.session() as session:
            result = session.run("MATCH (n) RETURN n.name AS name, labels(n) AS labels")
            return [r.data() for r in result]

    def get_all_edges(self):
        with self.driver.session() as session:
            result = session.run("MATCH (a)-[r]->(b) RETURN a.name AS src, type(r) AS rel, b.name AS dst")
            return [r.data() for r in result]

    def clear_all(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
