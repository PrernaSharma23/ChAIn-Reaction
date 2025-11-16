from dataclasses import dataclass
from typing import Optional
import json
from datetime import datetime


def iso_now() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass
class GraphNode:
    uid: str               # "repo:rel/path:kind:name"
    repo: str
    kind: str              # repo, file, class, method, table, sql_read, sql_write, topic, etc.
    name: str
    language: str
    path: str
    meta: str              # JSON string - keeping as string to avoid Neo4j map errors for now
    created_at: str

    @classmethod
    def from_dict(cls, d: dict):
        # Accept either 'meta' as dict or string and normalize to string
        meta = d.get("meta", "{}")
        if not isinstance(meta, str):
            try:
                meta = json.dumps(meta)
            except Exception:
                meta = json.dumps({"raw": str(meta)})
        created_at = d.get("created_at") or iso_now()
        return cls(
            uid=d["uid"],
            repo=d.get("repo", ""),
            kind=d.get("kind", ""),
            name=d.get("name", ""),
            language=d.get("language", ""),
            path=d.get("path", ""),
            meta=meta,
            created_at=created_at,
        )


@dataclass
class GraphEdge:
    src: str
    dst: str
    type: str    # CONTAINS, DEPENDS_ON, READS_FROM, WRITES_TO

    ALLOWED = {"CONTAINS", "DEPENDS_ON", "READS_FROM", "WRITES_TO"}

    def __post_init__(self):
        self.type = (self.type or "").upper()
        if self.type not in self.ALLOWED:
            raise ValueError(f"Invalid edge type: {self.type}. Allowed: {sorted(self.ALLOWED)}")

    @classmethod
    def from_tuple(cls, t):
        # t expected as (src, dst, type)
        return cls(src=t[0], dst=t[1], type=t[2])
