import os
from typing import List, Dict, Any, Tuple
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from src.model.graph_model import GraphNode, GraphEdge

BATCH_SIZE = 200  # pls change

class Neo4jRepository:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        pwd = os.getenv("NEO4J_PASS", "test123")
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, pwd))
            # quick sanity check
            with self.driver.session() as s:
                s.run("RETURN 1")
        except ServiceUnavailable as e:
            raise ConnectionError(f"Unable to reach Neo4j at {uri}: {e}")

        # ensure constraints
        self._init_constraints()

    def close(self):
        self.driver.close()

    def _init_constraints(self):
        with self.driver.session() as s:
            s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (r:Repo) REQUIRE r.uid IS UNIQUE")
            s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.uid IS UNIQUE")

    # -------------------------
    # Store graph: batch nodes and edges
    # -------------------------
    def store_graph(self, nodes: List[GraphNode], edges: List[GraphEdge]):
        """
        Writes nodes and edges into the DB in batches.
        Repo nodes get label :Repo, others :Entity
        """
        if not nodes:
            return

        # Batch insert nodes using UNWIND
        node_dicts = []
        for n in nodes:
            node_dicts.append({
                "uid": n.uid,
                "repo": n.repo,
                "kind": n.kind,
                "name": n.name,
                "language": n.language,
                "path": n.path,
                "meta": n.meta,
                "created_at": n.created_at,
            })

        with self.driver.session() as s:
            for i in range(0, len(node_dicts), BATCH_SIZE):
                batch = node_dicts[i:i+BATCH_SIZE]
                s.run(
                    """
                    UNWIND $batch AS row
                    WITH row
                    CALL {
                      WITH row
                      // choose label dynamically by kind
                      WITH row,
                           CASE WHEN row.kind = 'repo' THEN 'Repo' ELSE 'Entity' END AS label
                      CALL apoc.create.node([label], {uid: row.uid}) YIELD node
                      RETURN node
                    } YIELD node
                    SET node += row
                    """,
                    batch=batch
                )

        # Edges (validate allowed types before calling this method)
        with self.driver.session() as s:
            edge_tuples = [{"src": e.src, "dst": e.dst, "type": e.type} for e in edges]
            for i in range(0, len(edge_tuples), BATCH_SIZE):
                batch = edge_tuples[i:i+BATCH_SIZE]
                # can't parameterize rel type in Cypher; use CASE + APOC or safe string assembly
                # use APOC's create.relationship for safety (apoc must be available). Fallback if not.
                s.run(
                    """
                    UNWIND $batch AS r
                    MATCH (a {uid: r.src}), (b {uid: r.dst})
                    CALL apoc.create.relationship(a, r.type, {}, b) YIELD rel
                    RETURN count(rel)
                    """,
                    batch=batch
                )

    # -------------------------
    # Read helpers
    # -------------------------
    def get_all_nodes(self) -> List[Dict[str, Any]]:
        q = "MATCH (n) RETURN n.uid AS uid, labels(n) AS labels, n.repo AS repo, n.kind AS kind, n.name AS name LIMIT 10000"
        with self.driver.session() as s:
            return [dict(record) for record in s.run(q)]

    def get_all_edges(self) -> List[Dict[str, Any]]:
        q = "MATCH (a)-[r]->(b) RETURN a.uid AS src, type(r) AS type, b.uid AS dst LIMIT 20000"
        with self.driver.session() as s:
            return [dict(record) for record in s.run(q)]

    def clear_all(self):
        with self.driver.session() as s:
            s.run("MATCH (n) DETACH DELETE n")

    # -------------------------
    # Repo-scoped helpers
    # -------------------------
    def get_nodes_by_repo(self, repo: str):
        q = "MATCH (n {repo:$repo}) RETURN n.uid AS uid, n.kind AS kind, n.name AS name, n.path AS path"
        with self.driver.session() as s:
            return [dict(r) for r in s.run(q, repo=repo)]

    def get_edges_for_repo(self, repo: str):
        q = """
        MATCH (a {repo:$repo})-[r]->(b {repo:$repo})
        RETURN a.uid AS src, type(r) AS type, b.uid AS dst
        """
        with self.driver.session() as s:
            return [dict(r) for r in s.run(q, repo=repo)]

    # -------------------------
    # Cross-repo edges
    # -------------------------
    def get_edges_between_repos(self, repo_a: str, repo_b: str):
        """
        Return edges where a.node.repo = repo_a AND b.node.repo = repo_b
        Also returns reverse direction if any.
        Output: list of dicts {src, type, dst}
        """
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

    # -------------------------
    # Find entity by simple name 
    # -------------------------
    def find_entities_by_name(self, name: str):
        q = "MATCH (n) WHERE n.name = $name RETURN n.uid AS uid, n.repo AS repo, n.kind AS kind LIMIT 50"
        with self.driver.session() as s:
            return [dict(r) for r in s.run(q, name=name)]
