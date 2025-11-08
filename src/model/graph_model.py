from dataclasses import dataclass
from typing import List

@dataclass
class Node:
    name: str
    type: str

@dataclass
class Edge:
    src: str
    dst: str
    rel: str

@dataclass
class GraphData:
    nodes: List[Node]
    edges: List[Edge]
