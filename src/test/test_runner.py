import os
import json
import shutil
import tempfile
import sys
from pathlib import Path

# Ensure project root is on sys.path so `import src...` works when running this file directly
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.processor.repo_processor import RepoProcessor
from src.repository.neo4j_repository import Neo4jRepository


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


def main():
    print("🔧 Creating fake test repo...")
    repo_path = build_fake_repo()
    repo_name = "test_repo"

    try:
        repo_proc = RepoProcessor()
        neo = Neo4jRepository()

        print("🗑 Clearing Neo4j…")
        neo.clear_all()

        print("🧩 Extracting AST…")
        nodes, edges = repo_proc.process("test_id", repo_path, repo_name)

        print(f"Extracted {len(nodes)} nodes, {len(edges)} edges")

        print("📥 Ingesting into Neo4j…")
        neo.store_graph(nodes, edges)

        print(":> TEST COMPLETED")

    finally:
        print("🧹 Cleaning temp repo...")
        shutil.rmtree(repo_path)


if __name__ == "__main__":
    main()
