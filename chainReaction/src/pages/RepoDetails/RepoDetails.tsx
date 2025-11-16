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

  // -----------------------------------------------------
  // 🔥 Fetch graph data from backend (single source of truth)
  // -----------------------------------------------------
  useEffect(() => {
    const fetchGraph = async () => {
      try {
        const token = sessionStorage.getItem("token");

        const repoIds = viewType === "intra"
          ? [primaryRepoId]
          : secondRepoId
            ? [primaryRepoId, secondRepoId]
            : [primaryRepoId];

        const res = await fetch("https://misty-mousy-unseparately.ngrok-free.dev/api/project/graph", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ repo_ids: repoIds }),
        });

        if (!res.ok) {
          console.error("Failed to fetch graph");
          return;
        }

        const data = await res.json();

        // API returns: { nodes: [...], edges: [...] }
        setLocalNodes(data.nodes || []);
        setLocalEdges(data.edges || []);

      } catch (err) {
        console.error("Graph fetch error:", err);
      }
    };

    fetchGraph();
  }, [primaryRepoId, secondRepoId, viewType]);
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
    if (!allowed.has(s.repoId ?? '') || !allowed.has(t.repoId ?? '')) {
      setAddEdgeMode(false);
      return;
    }

    setPendingEdge({ from: sourceId, to: targetId });
    setShowAddModal(true);
  };

  const handleConfirmAdd = async (type: string) => {
    if (!pendingEdge) return;

    const newEdge: EdgeDatum = {
      from: pendingEdge.from,
      to: pendingEdge.to,
      type,
    };

    // Optimistic local update
    setLocalEdges((prev) => [...prev, newEdge]);

    setPendingEdge(null);
    setShowAddModal(false);
    setAddEdgeMode(false);

    // TODO: send to backend when API is ready
  };

  const handleCancelAdd = () => {
    setShowAddModal(false);
    setPendingEdge(null);
    setAddEdgeMode(false);
  };

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
      />

      <AddDependencyModal
        isOpen={showAddModal}
        sourceId={pendingEdge?.from ?? null}
        targetId={pendingEdge?.to ?? null}
        nodes={localNodes}
        onConfirm={handleConfirmAdd}
        onCancel={handleCancelAdd}
      />
    </div>
  );
}
