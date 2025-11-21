import os
from neo4j import GraphDatabase
from src.util.logger import log

class ImpactService:
    """
    Computes the full transitive impact of a changed node:
    - follows CONTAINS, DEPENDS_ON, READS_FROM, WRITES_TO
    - works across repositories
    - prevents cycles
    """

    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASS", "test123")

        self.driver = GraphDatabase.driver(uri, auth=(user, password))

        # All valid actionable relationship types here
        self.allowed_rels = ["CONTAINS", "DEPENDS_ON", "READS_FROM", "WRITES_TO"]

    def close(self):
        if self.driver:
            self.driver.close()

    # Get impact of a node by uid
    def get_impacted_graph(self, delta: dict) -> list[dict]:
        modified_uids = [n["uid"] for n in delta.get("modified", [])]

        if not modified_uids:
            log.info("No modified nodes, no impact")
            return []
        impacted_map = {}
        for uid in modified_uids:
            impacted_nodes = self.get_impacted_nodes(uid)
            for node in impacted_nodes:
                impacted_map[node["uid"]] = node
        return list(impacted_map.values())
    
    def get_impact(self, delta:dict, external_only:bool=False) -> list[dict]:
        if external_only:
            return self.get_impacted_external_graph(delta)
        else:
            return self.get_impacted_graph(delta)
    
    def get_impacted_external_graph(self, delta: dict) -> list[dict]:
        """
        Like get_impacted_graph but only returns external impacted nodes
        (nodes whose repo_id differs from the start node). Accepts the same
        delta dict and returns a list[dict] of impacted node records.
        """
        modified_uids = [n["uid"] for n in delta.get("modified", [])]

        if not modified_uids:
            log.info("No modified nodes, no external impact")
            return []   

        impacted_map = {}
        for uid in modified_uids:
            impacted_nodes = self.get_impacted_external_nodes(uid)
            for node in impacted_nodes:
                impacted_map[node["uid"]] = node
        return list(impacted_map.values())
    

    def get_impacted_nodes(self, start_uid: str):
        """
        Returns full transitive impact of a starting node.
        Uses DFS-like expansion WITHIN Neo4j (no Python loops).
        Ignores invalid or stray edges automatically.
        """

        with self.driver.session() as session:
            result = session.execute_read(
                self._query_impact,
                start_uid,
                self.allowed_rels
            )
            return result

    def get_impacted_external_nodes(self, start_uid: str):
        """
        Returns impacted nodes reachable from start_uid that belong to a different repo_id than the start node.
        Same return format as get_impacted_nodes (list of dicts with uid, name, kind, repo_id, repo_name, path, language).
        Traverses up to 10 hops following only allowed relationship types and prevents cycles.
        """
        with self.driver.session() as session:
            result = session.execute_read(
                self._query_external_impact,
                start_uid,
                self.allowed_rels
            )
            return result

    # NEO4J QUERY
    @staticmethod
    def _query_impact(tx, start_uid, allowed_rels):
        """
        - Performs variable-length traversal across ONLY allowed rels
        - Avoids cycles
        - Returns ordered, unique nodes
        - Includes repo-level, file-level, class-level, method-level, table-level nodes
        """

        # Convert Python list → syntax: [:A|B|C] (only first colon, then pipe without colons)
        rel_union = "|".join([r if i == 0 else r for i, r in enumerate(allowed_rels)])
        rel_union = f":{rel_union}"

        query = """
        MATCH (start {uid: $start_uid})
        MATCH p = (start)-[rels*1..10]-(n)
        WHERE n.repo_id IS NOT NULL
          AND ALL(r IN rels WHERE type(r) IN $allowed_rels)
          AND ALL(i IN RANGE(0, SIZE(rels)-1) WHERE
                (
                  type(rels[i]) = 'CONTAINS'
                )
                OR (
                  (type(rels[i]) = 'DEPENDS_ON' OR type(rels[i]) = 'READS_FROM' OR type(rels[i]) = 'WRITES_TO')
                  AND endNode(rels[i]) = nodes(p)[i]
                )
              )
          AND ALL(x IN nodes(p) WHERE x IS NOT NULL)
        RETURN DISTINCT n.uid AS uid,
                        n.name AS name,
                        n.kind AS kind,
                        n.repo_id AS repo_id,
                        n.repo_name AS repo_name,
                        n.path AS path,
                        n.language AS language,
                        length(p) AS depth
        ORDER BY n.repo_id, depth, kind, name
        """
        result = tx.run(query, start_uid=start_uid, allowed_rels=allowed_rels)
        return [record.data() for record in result]

    @staticmethod
    def _query_external_impact(tx, start_uid, allowed_rels):
        """
        Find impacted nodes reachable from start_uid that belong to a different repo_id.
        Enforce directionality per relationship type to follow impact flow:
          - CONTAINS: follow from container -> contained (startNode(rel) = current node)
          - DEPENDS_ON, READS_FROM, WRITES_TO: follow from dependent -> dependency
            so when propagating impact we traverse the relationship in the direction
            that yields the dependent node (endNode(rel) = next node in path).
        """
        query = """
        MATCH (start {uid: $start_uid})
        MATCH p = (start)-[rels*1..10]-(n)
        WHERE n.repo_id IS NOT NULL
          AND n.repo_id <> start.repo_id
          AND ALL(r IN rels WHERE type(r) IN $allowed_rels)
          AND ALL(i IN RANGE(0, SIZE(rels)-1) WHERE
                (
                  type(rels[i]) = 'CONTAINS'                 )
                OR (
                  (type(rels[i]) = 'DEPENDS_ON' OR type(rels[i]) = 'READS_FROM' OR type(rels[i]) = 'WRITES_TO' OR type(rels[i]) = 'CONTAINS' )
                  AND endNode(rels[i]) = nodes(p)[i]
                )
              )
          AND ALL(x IN nodes(p) WHERE x IS NOT NULL)
        RETURN DISTINCT n.uid AS uid,
                        n.name AS name,
                        n.kind AS kind,
                        n.repo_id AS repo_id,
                        n.repo_name AS repo_name,
                        n.path AS path,
                        n.language AS language,
                        length(p) AS depth
        ORDER BY n.repo_id, depth, kind, name
        """
        result = tx.run(query, start_uid=start_uid, allowed_rels=allowed_rels)
        return [record.data() for record in result]