# ChAIn-Reaction
AI-driven impact analysis tool that automates detection of dependencies, risk, and scope of change in complex applications.

# Required
python 3.12.8


### Components Overview

| Component | Description |
|------------|-------------|
| `tree_sitter_extractor.py` | Parses code files (Python, Java) using Tree-sitter and extracts function/class symbols. |
| `diff_processor.py` | Uses Git diff to find changed files and functions. Maps changes to impacted nodes. |
| `neo4j_ingest.py` | Creates nodes (`File`, `Function`) and `CONTAINS`/`CALLS` edges in Neo4j. |
| `requirements.txt` | Dependencies list for setup. |

"""
##Minimal architecture diagram (ASCII)

   [Git Repo / PR] --webhook--> [Diff Processor] ---> [Tree-sitter Extractor]
                                            |                   |
                                            |                   v
                                            |               [Symbol Graph]
                                            v
                                       [Impact Engine]
                                            |
                                            v
                                         [Neo4j]
                                            |
                                            v
                                          [UI / API]

---


Notes:
 - Diff Processor: clones repo (or uses local path), computes git diff between base and head commit, extracts changed files and changed line ranges, and invokes symbol extractor to map line ranges -> symbols.
 - Tree-sitter Extractor: uses tree-sitter grammars for Java and Python to parse files and produce function/class symbols with name and line ranges.
 - Neo4j Ingest: creates basic nodes (File, Function) and 'contains' / 'calls' edges (initially only 'contains' for MVP).

Usage:
 - Fill in Git credentials or run on local clone.
 - Run tree_sitter_extractor to parse repo files and output symbols.json (or stream to Neo4j).
 - Run diff_processor with base and head commit to get changed symbols.

# Impact Analysis Starter


### Setup
1. Clone repo and install deps:
```bash
pip install -r requirements.txt
```
2. Build Tree-sitter languages:
```bash
mkdir -p build vendor
git clone https://github.com/tree-sitter/tree-sitter-python vendor/tree-sitter-python
git clone https://github.com/tree-sitter/tree-sitter-java vendor/tree-sitter-java
```
3. Run extractor:
```bash
python tree_sitter_extractor.py example.py
```
4. Ingest into Neo4j:
```bash
python neo4j_ingest.py
```
```


---