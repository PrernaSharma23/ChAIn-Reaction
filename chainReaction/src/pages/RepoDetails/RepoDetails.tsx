// RepoDetails.tsx
import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import GraphCanvas from "./GraphCanvas";
import SidePanel from "./SidePanel";
import AddDependencyModal from "./AddDependencyModal";

import type { NodeDatum, EdgeDatum } from "./types";
import "./RepoDetails.scss";

import { getAllRepoIds } from "./Utils";

export default function RepoDetails() {
  const { repoId } = useParams();
  const primaryRepoId = repoId ?? "";

  const [viewType, setViewType] = useState<"intra" | "inter">("intra");
  const [secondRepoId, setSecondRepoId] = useState<string | null>(null);
  const [showRepoPicker, setShowRepoPicker] = useState(false);

  const [addEdgeMode, setAddEdgeMode] = useState(false);
  const [pendingEdge, setPendingEdge] = useState<{ from: string; to: string } | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  // The REAL graph data now comes from API only
  const [localNodes, setLocalNodes] = useState<NodeDatum[]>([]);
  const [localEdges, setLocalEdges] = useState<EdgeDatum[]>([]);

  // Loader
  const [loading, setLoading] = useState(true);

  // -----------------------------------------------------
  // 🔥 Fetch graph data from backend (single source of truth)
  // -----------------------------------------------------
  useEffect(() => {
    const fetchGraph = async () => {
      try {
        setLoading(true); // <-- START loader

        const token = sessionStorage.getItem("token");

        const repoIds =
          viewType === "intra"
            ? [primaryRepoId]
            : secondRepoId
              ? [primaryRepoId, secondRepoId]
              : [primaryRepoId];

        const res = await fetch(
          "https://misty-mousy-unseparately.ngrok-free.dev/api/project/graph",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ repo_ids: repoIds }),
          }
        );

        if (!res.ok) {
          console.error("Failed to fetch graph");
          setLoading(false);
          return;
        }

        const data = await res.json();

        // API returns: { nodes: [...], edges: [...] }
        setLocalNodes(data.nodes || []);
        setLocalEdges(data.edges || []);

        setLoading(false); // <-- STOP loader

      } catch (err) {
        console.error("Graph fetch error:", err);
        setLoading(false); // <-- STOP loader on error
      }
    };

    fetchGraph();
  }, [primaryRepoId, secondRepoId]);
  // -----------------------------------------------------

  // Drag-complete callback from GraphCanvas
  const handleEdgeDragComplete = (sourceId: string, targetId: string) => {
    const s = localNodes.find((n) => n.id === sourceId);
    const t = localNodes.find((n) => n.id === targetId);
    if (!s || !t) return;

    // disallow intra dependencies
    if (s.repoId === t.repoId) {
      setAddEdgeMode(false);
      return;
    }

    if (viewType !== "inter" || !secondRepoId) {
      setAddEdgeMode(false);
      return;
    }

    const allowed = new Set([primaryRepoId, secondRepoId]);
    if (!allowed.has(s.repoId ?? "") || !allowed.has(t.repoId ?? "")) {
      setAddEdgeMode(false);
      return;
    }

    setPendingEdge({ from: sourceId, to: targetId });
    setShowAddModal(true);
  };

  const handleConfirmAdd = async (
    type: string,
    fromOverride?: string,
    toOverride?: string
  ) => {
    if (!pendingEdge && (!fromOverride || !toOverride)) {
      return;
    }

    const from = fromOverride ?? pendingEdge?.from ?? '';
    const to = toOverride ?? pendingEdge?.to ?? '';

    const newEdge: EdgeDatum = {
      from,
      to,
      type,
    };

    // Close modal immediately (UX)
    setPendingEdge(null);
    setShowAddModal(false);
    setAddEdgeMode(false);

    try {
      const token = sessionStorage.getItem("token");
      const response = await fetch("https://misty-mousy-unseparately.ngrok-free.dev/api/project/edge", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`, // <-- ensure token variable exists
        },
        body: JSON.stringify({
          from,
          to,
          type,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to add edge");
      }

      // Now update local edges only on success
      setLocalEdges((prev) => [...prev, newEdge]);

    } catch (err) {
      console.error("Error adding edge:", err);
    }
  };

  const openManualDependencyModal = () => {
    setPendingEdge(null);        // no from/to (manual)
    setAddEdgeMode(false);       // turn off drag mode
    setShowAddModal(true);       // open modal immediately
  };

  const handleCancelAdd = () => {
    setShowAddModal(false);
    setPendingEdge(null);
    setAddEdgeMode(false);
  };

  // loader UI
  if (loading) {
    return (
      <div className="graph-loader">
        <div className="spinner"></div>
        <p>Loading graph...</p>
      </div>
    );
  }

  return (
    <div className="repo-page-wrapper" style={{ display: "flex", gap: 0 }}>
      <GraphCanvas
        key={localEdges.length}
        graphData={{ nodes: localNodes, edges: localEdges }}
        addEdgeMode={addEdgeMode}
        onEdgeDragComplete={handleEdgeDragComplete}
        primaryRepoId={primaryRepoId}
        secondRepoId={secondRepoId}
        selectedNodeId={selectedNodeId}
        setSelectedNodeId={setSelectedNodeId}
      />

      <SidePanel
        primaryRepoId={primaryRepoId}
        viewType={viewType}
        setViewType={(v) => {
          setViewType(v);
          if (v === "intra") {
            setSecondRepoId(null);
            setShowRepoPicker(false);
          }
          setAddEdgeMode(false);
          setSelectedNodeId(null);
        }}
        secondRepoId={secondRepoId}
        setSecondRepoId={(r) => {
          setSecondRepoId(r);
          setSelectedNodeId(null);
        }}
        showRepoPicker={showRepoPicker}
        setShowRepoPicker={setShowRepoPicker}
        allReposIds={getAllRepoIds()}
        addEdgeMode={addEdgeMode}
        setAddEdgeMode={setAddEdgeMode}
        openManualDependencyModal={openManualDependencyModal} 
      />

      <AddDependencyModal
        isOpen={showAddModal}
        sourceId={pendingEdge?.from ?? null}
        targetId={pendingEdge?.to ?? null}
        primaryRepoId={primaryRepoId}
        secondRepoId={secondRepoId}
        nodes={localNodes}
        onConfirm={handleConfirmAdd}
        onCancel={handleCancelAdd}
      />
    </div>
  );
}
