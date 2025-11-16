import React, { useMemo, useState, useEffect } from "react";
import "./AddDependencyModal.scss";
import type { NodeDatum } from "./types";

export default function AddDependencyModal({
  isOpen,
  sourceId,
  targetId,
  nodes,
  onConfirm,
  onCancel,
}: {
  isOpen: boolean;
  sourceId: string | null;
  targetId: string | null;
  nodes: NodeDatum[];
  onConfirm: (type: string) => void;
  onCancel: () => void;
}) {
  const [type, setType] = useState<string | null>(null);

  // ⭐ RESET TYPE every time modal opens
  useEffect(() => {
    if (isOpen) setType(null);
  }, [isOpen]);

  const source = useMemo(
    () => nodes.find((n) => n.id === sourceId) ?? null,
    [nodes, sourceId]
  );

  const target = useMemo(
    () => nodes.find((n) => n.id === targetId) ?? null,
    [nodes, targetId]
  );

  if (!isOpen) return null;

  return (
    <div className="adm-overlay">
      <div className="adm-card">
        <h3 className="adm-title">Create Dependency</h3>

        <div className="adm-row">
          <div>
            <div className="label">Source</div>
            <div className="chip">{source ? `${source.id} • ${source.type}` : "-"}</div>
          </div>

          <div className="arrow">→</div>

          <div>
            <div className="label">Target</div>
            <div className="chip">{target ? `${target.id} • ${target.type}` : "-"}</div>
          </div>
        </div>

        <div className="adm-field">
          <div className="label">Dependency Type</div>

          <div className="type-options">
            {["CALLS", "READS", "WRITES", "DEPENDS_ON"].map((t) => (
              <button
                key={t}
                className={`type-pill ${type === t ? "selected" : ""}`}
                onClick={() => setType(t)}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        <div className="adm-actions">
          <button className="adm-btn-cancel" onClick={onCancel}>Cancel</button>

          <button
            className="adm-btn-confirm"
            disabled={!type}
            onClick={() => type && onConfirm(type)}
          >
            Create Dependency
          </button>
        </div>
      </div>
    </div>
  );
}
