import os
from neo4j import GraphDatabase

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

    # -------------------------------------------------------
    # Get impact of a node by uid
    # -------------------------------------------------------
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

    # -------------------------------------------------------
    # NEO4J QUERY
    # -------------------------------------------------------
    @staticmethod
    def _query_impact(tx, start_uid, allowed_rels):
        """
        - Performs variable-length traversal across ONLY allowed rels
        - Avoids cycles
        - Returns ordered, unique nodes
        - Includes repo-level, file-level, class-level, method-level, table-level nodes
        """

        # Convert Python list → syntax: [:A|:B|:C]
        rel_union = "|".join([f":{r}" for r in allowed_rels])

        query = f"""
        MATCH (start {{uid: $start_uid}})
        CALL {{
            WITH start
            MATCH p = (start)-[{rel_union}*1..10]->(n)
            WHERE ALL(x IN nodes(p) WHERE x IS NOT NULL)
            RETURN DISTINCT n
        }}
        RETURN DISTINCT n.uid AS uid,
                       n.name AS name,
                       n.kind AS kind,
                       n.repo AS repo,
                       n.path AS path,
                       n.language AS language
        ORDER BY kind, name
        """

        result = tx.run(query, start_uid=start_uid)
        return [record.data() for record in result]
