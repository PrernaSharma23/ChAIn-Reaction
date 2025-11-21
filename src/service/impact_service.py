import os
from neo4j import GraphDatabase
from src.util.logger import log

class ImpactService:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASS", "test123")

        self.driver = GraphDatabase.driver(uri, auth=(user, password))

        self.allowed_rels = ["CONTAINS", "DEPENDS_ON", "READS_FROM", "WRITES_TO"]

    def close(self):
        if self.driver:
            self.driver.close()

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
        with self.driver.session() as session:
            result = session.execute_read(
                self._query_impact,
                start_uid,
                self.allowed_rels
            )
            return result

    def get_impacted_external_nodes(self, start_uid: str):
        with self.driver.session() as session:
            result = session.execute_read(
                self._query_external_impact,
                start_uid,
                self.allowed_rels
            )
            return result

    @staticmethod
    def _query_impact(tx, start_uid, allowed_rels):
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