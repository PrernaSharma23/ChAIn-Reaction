from neo4j import GraphDatabase
import os
from src.util.logger import log
from typing import List


class GraphDeltaService:

    def __init__(self):
        uri = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        pwd = os.getenv("NEO4J_PASS")
        self.driver = GraphDatabase.driver(uri, auth=(user, pwd))
    

    def get_repo_nodes(self, repo_id: str) -> List[str]:
        q = """
        MATCH (n {repo_id:$repo_id})
        RETURN n.uid AS uid
        """
        with self.driver.session() as s:
            return [r['uid'] for r in s.run(q, repo_id=repo_id)]

    def compute_delta(self, pr_nodes: List[dict], pr_edges: List[dict]) -> dict:

        if not pr_nodes:
            log.info("No PR nodes provided")
            return {"added": [], "modified": []}

        try:
            repo_id = pr_nodes[0].get("repo_id")
            
            if not repo_id:
                log.warning("No repo_id in first PR node")
                return {"error": "Missing repo_id", "added": [], "modified": []}

            pr_node_map = {n.get("uid"): n for n in pr_nodes if n.get("uid")}
            pr_uids = set(pr_node_map.keys())

            base_uids = set(self.get_repo_nodes(repo_id))

            # nodes in PR but not in base
            added_uids = pr_uids - base_uids
            added = [pr_node_map[uid] for uid in added_uids]

            # nodes in both PR and base
            modified_uids = pr_uids & base_uids
            modified = [ pr_node_map[uid] for uid in modified_uids ]  
            log.info(f"Delta summary: +{len(added)} added, ~{len(modified)} modified")

            return {
                "added": added,
                "modified": modified
            }

        except Exception as e:
            log.error(f"Error computing delta: {e}")
            return {"error": str(e), "added": [], "modified": []}
