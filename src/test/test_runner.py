#!/usr/bin/env python3
"""
Full MVP integration test:
1. Creates a tiny fake repo (Java + Python)
2. Extracts AST -> entities & edges
3. Ingests into Neo4j
4. Runs impact analysis -- PENDING
5. Runs explanation LLM -- PENDING
"""

import os
import json
import tempfile
import shutil

from src.processor.repo_processor import RepoProcessor
from src.repository.neo4j_repository import Neo4jRepository

# -----------------------------
# Step 1 — Build a dummy repo
# -----------------------------
def build_fake_repo():
    repo_dir = tempfile.mkdtemp(prefix="fake_repo_")

    java_file = os.path.join(repo_dir, "TestService.java")
    py_file = os.path.join(repo_dir, "processor.py")

    with open(java_file, "w") as f:
        f.write("""
package com.example;

public class TestService {
    public User getTest(int id) {
        String q = "SELECT * FROM test WHERE id = " + id;
        return null;
    }

    public void updateTest(Test t) {
        String q = "UPDATE test SET name = 'x' WHERE id = " + t.id;
    }
}
""")

    with open(py_file, "w") as f:
        f.write("""
def compute(x):
    return x + 1

def do_write():
    query = "UPDATE table SET a=1"
""")

    return repo_dir


# -----------------------------
# Step 2 — Full pipeline test
# -----------------------------
def main():
    print("🔧 Creating fake test repo...")
    repo_path = build_fake_repo()
    repo_name = "test_repo"

    try:
        repo_proc = RepoProcessor()
        neo = Neo4jRepository()

        # completely clear DB for fresh test
        print("🗑 Clearing Neo4j...")
        neo.clear_all()

        # extract graph from fake repo
        print("🧩 Extracting entities/edges...")
        entities, edges = repo_proc.process(repo_name, repo_path)

        print(f"Entities extracted: {len(entities)}")
        print(f"Edges extracted: {len(edges)}")

        # store in DB
        print("📥 Ingesting into Neo4j...")
        neo.store_graph({"entities": entities, "edges": edges})

        print(":> All done!")

    finally:
        print("🧹 Cleaning temp repo...")
        shutil.rmtree(repo_path)


if __name__ == "__main__":
    main()
