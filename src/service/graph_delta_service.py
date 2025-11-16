from neo4j import GraphDatabase
import os

class GraphDeltaService:

    def __init__(self):
        uri = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        pwd = os.getenv("NEO4J_PASS")
        
        self.driver = GraphDatabase.driver(uri, auth=(user, pwd ))

    # --- BASIC HELPERS -----------------------------------------------------

    def node_exists(self, uid):
        q = "MATCH (n {uid:$uid}) RETURN n LIMIT 1"
        with self.driver.session() as s:
            return s.run(q, uid=uid).single() is not None

    def get_existing_edges(self, uid):
        q = """
        MATCH (n {uid:$uid})-[r]->(m)
        RETURN type(r) as type, m.uid as target
        """
        with self.driver.session() as s:
            return {(record["type"], record["target"]) for record in s.run(q, uid=uid)}

    # --- THE DELTA ALGORITHM ----------------------------------------------

    def compute_delta(self, pr_nodes, pr_edges):
        added = []
        modified = []
        unchanged = []

        # 1. classify nodes
        for n in pr_nodes:
            uid = n["uid"]

            if not self.node_exists(uid):
                added.append(n)
                continue

            # Check if modified: compare meta or name or kind
            unchanged.append(uid)  # tentative

        # 2. detect deleted nodes (present in base but missing in PR diff)
        deleted = self._detect_deleted_nodes(unchanged)

        # 3. detect modified nodes using edge diff
        modified = self._detect_modified_edges(pr_edges)

        return {
            "added": added,
            "modified": modified,
            "deleted": deleted
        }

    def _detect_deleted_nodes(self, pr_uids):
        q = """
        MATCH (n)
        WHERE n.uid STARTS WITH $repo   // limit to repo
        RETURN n.uid AS uid
        """

        with self.driver.session() as s:
            base_uids = [r["uid"] for r in s.run(q, repo="repo:")]  # adjust for real repo

        return [u for u in base_uids if u not in pr_uids]

    def _detect_modified_edges(self, pr_edges):
        modified_nodes = {}

        # group edges by source uid
        edges_by_node = {}
        for (src, tgt, rel) in pr_edges:
            edges_by_node.setdefault(src, set()).add((rel, tgt))

        for src_uid, new_edges in edges_by_node.items():
            if not self.node_exists(src_uid):
                continue

            old_edges = self.get_existing_edges(src_uid)

            if old_edges != new_edges:
                modified_nodes[src_uid] = {
                    "old_edges": list(old_edges),
                    "new_edges": list(new_edges)
                }

        return modified_nodes
