import os
import sys
import shutil
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from neo4j import GraphDatabase

from src.processor.repo_processor import RepoProcessor
from src.repository.neo4j_repository import Neo4jRepository
from src.model.graph_model import GraphEdge, GraphNode
from src.service.impact_service import ImpactService


def write_java_service(base_dir: str, repo_label: str):
    os.makedirs(base_dir, exist_ok=True)
    java_file = os.path.join(base_dir, "Service.java")
    with open(java_file, "w") as f:
        f.write(f"""
package com.example.{repo_label.lower()};

public class Service{repo_label} {{
    public void do{repo_label}() {{
        String q = "SELECT * FROM table_{repo_label}";
    }}

    public void helper{repo_label}() {{
        // helper
    }}
}}
""")
    return java_file


def write_python_utils(base_dir: str, repo_label: str):
    os.makedirs(base_dir, exist_ok=True)
    py_file = os.path.join(base_dir, "utils.py")
    with open(py_file, "w") as f:
        f.write(f"""
def compute_{repo_label.lower()}(x):
    return x + 1

def write_{repo_label.lower()}():
    q = "UPDATE table_{repo_label} SET a=1"
""")
    return py_file


def collect_and_normalize(repo_proc: RepoProcessor, repo_id: str, repo_name: str, repo_path: str):
    nodes, edges = repo_proc.process(repo_id, repo_path, repo_name)
    normalized = []
    for n in nodes:
        if isinstance(n, GraphNode):
            if not getattr(n, "repo_id", None):
                n.repo_id = repo_id
            if not getattr(n, "repo_name", None):
                n.repo_name = repo_name
            normalized.append(n)
        else:
            d = n if isinstance(n, dict) else n.to_dict()
            d["repo_id"] = d.get("repo_id") or repo_id
            d["repo_name"] = d.get("repo_name") or repo_name
            normalized.append(GraphNode.from_dict(d))
    return normalized, edges


def find_method_node(nodes, candidate_names):
    for n in nodes:
        if getattr(n, "kind", "").lower() == "method" and getattr(n, "name", "") in candidate_names:
            return n
    return None


def test_cross_repo_external_impact_ast():
    tmp_root = tempfile.mkdtemp(prefix="crossrepo_test_")
    neo = Neo4jRepository()
    neo.clear_all()
    repo_proc = RepoProcessor()

    try:
        # create repo folders and files
        repoA_dir = os.path.join(tmp_root, "repoA")
        repoB_dir = os.path.join(tmp_root, "repoB")
        repoC_dir = os.path.join(tmp_root, "repoC")

        write_java_service(repoA_dir, "A")
        write_java_service(repoB_dir, "B")
        write_python_utils(repoC_dir, "C")

        # extract and normalize each repo independently
        nodes_a, edges_a = collect_and_normalize(repo_proc, "repoA", "Repo A", repoA_dir)
        nodes_b, edges_b = collect_and_normalize(repo_proc, "repoB", "Repo B", repoB_dir)
        nodes_c, edges_c = collect_and_normalize(repo_proc, "repoC", "Repo C", repoC_dir)

        # ingest each repo separately
        neo.store_graph(nodes_a, edges_a)
        neo.store_graph(nodes_b, edges_b)
        neo.store_graph(nodes_c, edges_c)

        # locate method nodes (names depend on extractor naming)
        a_method = find_method_node(nodes_a, ["doA", "doA()"])
        b_method = find_method_node(nodes_b, ["doB", "doB()", "useB", "useA"])
        c_method = find_method_node(nodes_c, ["compute_c", "write_c", "compute_C", "write_C"])

        assert a_method is not None
        assert b_method is not None
        assert c_method is not None

        # persist cross-repo DEPENDS_ON relationships explicitly so edges exist
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASS", "test123")
        drv = GraphDatabase.driver(uri, auth=(user, password))
        try:
            with drv.session() as session:
                session.run(
                    "MATCH (b {uid:$b_uid}), (a {uid:$a_uid}) MERGE (b)-[:DEPENDS_ON]->(a)",
                    b_uid=b_method.uid, a_uid=a_method.uid
                )
                session.run(
                    "MATCH (c {uid:$c_uid}), (b {uid:$b_uid}) MERGE (c)-[:DEPENDS_ON]->(b)",
                    c_uid=c_method.uid, b_uid=b_method.uid
                )
        finally:
            drv.close()

        svc = ImpactService()
        try:
            impacted = svc.get_impacted_external_nodes(a_method.uid)
        finally:
            svc.close()

        repo_ids = {n.get("repo_id") for n in impacted}
        uids = {n.get("uid") for n in impacted}

        assert "repoB" in repo_ids
        assert "repoC" in repo_ids
        assert b_method.uid in uids
        assert c_method.uid in uids

    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__])