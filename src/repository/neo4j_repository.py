import os
from typing import List, Dict, Any
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from src.model.graph_model import GraphNode, GraphEdge

BATCH_SIZE = 200

"""
Optimization needed
"""
class Neo4jRepository:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        pwd = os.getenv("NEO4J_PASS")
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, pwd))
            with self.driver.session() as s:
                s.run("RETURN 1")
        except ServiceUnavailable as e:
            raise ConnectionError(f"Cannot connect to Neo4j at {uri}: {e}")

        self._init_constraints()

    def close(self):
        self.driver.close()

    def _init_constraints(self):
        with self.driver.session() as s:
            s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (r:Repo) REQUIRE r.uid IS UNIQUE")
            s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.uid IS UNIQUE")

    # PURE INGESTION 
    def store_graph(self, nodes: List[GraphNode], edges: List[GraphEdge]):
        if not nodes:
            return

        # ---- Process Nodes ----
        node_dicts = []
        for n in nodes:
            node_dicts.append({
                "uid": n.uid,
                "repo_id": n.repo_id,
                "repo_name": n.repo_name,
                "kind": n.kind,
                "name": n.name,
                "language": n.language,
                "path": n.path,
                "meta": n.meta,
                "created_at": n.created_at,
            })

        with self.driver.session() as session:
            for i in range(0, len(node_dicts), BATCH_SIZE):
                batch = node_dicts[i:i+BATCH_SIZE]

                session.run(
                    """
                    UNWIND $batch AS row
                    MERGE (n {uid: row.uid})
                    SET n += row

                    // label assignment using conditional FOREACH
                    WITH n, row,
                        CASE WHEN row.kind = 'repo' THEN 'Repo' ELSE 'Entity' END AS label

                    FOREACH (_ IN CASE WHEN label = 'Repo' THEN [1] ELSE [] END |
                        SET n:Repo
                    )
                    FOREACH (_ IN CASE WHEN label <> 'Repo' THEN [1] ELSE [] END |
                        SET n:Entity
                    )
                    """,
                    batch=batch
                )

        # ---- Process Edges ----
        with self.driver.session() as session:
            for e in edges:
                q = f"""
                MATCH (a {{uid: $src}})
                MATCH (b {{uid: $dst}})
                MERGE (a)-[:{e.type}]->(b)
                """
                session.run(q, src=e.src, dst=e.dst)

    # READ HELPERS
    def get_all_nodes(self):
        q = """
        MATCH (n)
        RETURN n.uid AS uid, labels(n) AS labels,
               n.repo AS repo, n.kind AS kind, n.name AS name
        LIMIT 10000
        """
        with self.driver.session() as s:
            return [dict(record) for record in s.run(q)]

    def get_all_edges(self):
        q = """
        MATCH (a)-[r]->(b)
        RETURN a.uid AS src, type(r) AS type, b.uid AS dst
        LIMIT 20000
        """
        with self.driver.session() as s:
            return [dict(record) for record in s.run(q)]

    def clear_all(self):
        with self.driver.session() as s:
            s.run("MATCH (n) DETACH DELETE n")

    # REPO-SCOPED
    def get_nodes_by_repo(self, repo: str):
        q = """
        MATCH (n {repo:$repo})
        RETURN n.uid AS uid, n.kind AS kind, n.name AS name, n.path AS path
        """
        with self.driver.session() as s:
            return [dict(r) for r in s.run(q, repo=repo)]

    def get_edges_for_repo(self, repo: str):
        q = """
        MATCH (a {repo:$repo})-[r]->(b {repo:$repo})
        RETURN a.uid AS src, type(r) AS type, b.uid AS dst
        """
        with self.driver.session() as s:
            return [dict(r) for r in s.run(q, repo=repo)]

    # CROSS-REPO-SCOPED
    def get_edges_between_repos(self, repo_a: str, repo_b: str):
        q = """
        MATCH (a {repo:$repo_a})-[r]->(b {repo:$repo_b})
        RETURN a.uid AS src, type(r) AS type, b.uid AS dst
        """
        with self.driver.session() as s:
            forward = [dict(r) for r in s.run(q, repo_a=repo_a, repo_b=repo_b)]

        q_rev = """
        MATCH (a {repo:$repo_b})-[r]->(b {repo:$repo_a})
        RETURN a.uid AS src, type(r) AS type, b.uid AS dst
        """
        with self.driver.session() as s:
            backward = [dict(r) for r in s.run(q_rev, repo_a=repo_a, repo_b=repo_b)]

        return {"forward": forward, "backward": backward}

    def find_entities_by_name(self, name: str):
        q = """
        MATCH (n)
        WHERE n.name = $name
        RETURN n.uid AS uid, n.repo AS repo, n.kind AS kind
        LIMIT 50
        """
        with self.driver.session() as s:
            return [dict(r) for r in s.run(q, name=name)]
