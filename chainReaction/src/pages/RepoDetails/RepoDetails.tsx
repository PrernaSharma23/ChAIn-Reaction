// RepoDetails.tsx
import React, { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import mockGraphData from "./mockGraphData";
import GraphCanvas from "./GraphCanvas";
import SidePanel from "./SidePanel";
import AddDependencyModal from "./AddDependencyModal";
import type { NodeDatum, EdgeDatum } from "./types";
import "./RepoDetails.scss";
import { getAllRepoIds } from "./Utils";

export default function RepoDetails() {
  const { repoId } = useParams();

  // repoName is actually repoId from the URL
  const primaryRepoId = repoId ?? "";

  const [viewType, setViewType] = useState<"intra" | "inter">("intra");
  const [secondRepoId, setSecondRepoId] = useState<string | null>(null);
  const [showRepoPicker, setShowRepoPicker] = useState(false);

  // Add-dependency workflow
  const [addEdgeMode, setAddEdgeMode] = useState(false);
  const [pendingEdge, setPendingEdge] = useState<{ from: string; to: string } | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);

  // NEW: which node is selected for highlight (null = none)
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  // Load all nodes + edges from mock data
  const initial = useMemo(() => {
    const nodes: NodeDatum[] = [];

    for (const key of Object.keys(mockGraphData)) {
      if (key.toLowerCase().includes("nodes")) {
        const arr = (mockGraphData as any)[key] as NodeDatum[];
        if (Array.isArray(arr)) nodes.push(...arr);
      }
    }

    const edges: EdgeDatum[] = mockGraphData.edges ?? [];
    return { nodes, edges };
  }, []);

  const [localNodes, setLocalNodes] = useState<NodeDatum[]>(initial.nodes);
  const [localEdges, setLocalEdges] = useState<EdgeDatum[]>(initial.edges);

  // Filtered graph data based on viewType
  const filteredGraphData = useMemo(() => {
    if (viewType === "intra") {
      const nodes = localNodes.filter((n) => n.repo === primaryRepoId);
      const allowed = new Set(nodes.map((n) => n.id));
      const edges = localEdges.filter((e) => allowed.has(e.from) && allowed.has(e.to));
      return { nodes, edges };
    }

    const nodes = localNodes.filter(
      (n) => n.repo === primaryRepoId || n.repo === secondRepoId
    );

    const allowed = new Set(nodes.map((n) => n.id));
    const edges = localEdges.filter(
      (e) => allowed.has(e.from) && allowed.has(e.to)
    );

    return { nodes, edges };
  }, [localNodes, localEdges, viewType, primaryRepoId, secondRepoId]);

  // Called by GraphCanvas on drag completion
  const handleEdgeDragComplete = (sourceId: string, targetId: string) => {
    const s = localNodes.find((n) => n.id === sourceId);
    const t = localNodes.find((n) => n.id === targetId);
    if (!s || !t) return;

    // disallow intra
    if (s.repo === t.repo) {
      setAddEdgeMode(false);
      return;
    }

    // only inter view + secondRepo selected
    if (viewType !== "inter" || !secondRepoId) {
      setAddEdgeMode(false);
      return;
    }

    const allowedRepos = new Set([primaryRepoId, secondRepoId]);
    if (!allowedRepos.has(s.repo ?? "") || !allowedRepos.has(t.repo ?? "")) {
      setAddEdgeMode(false);
      return;
    }

    setPendingEdge({ from: sourceId, to: targetId });
    setShowAddModal(true);
  };

  // Confirm add
  const handleConfirmAdd = async (type: string) => {
    if (!pendingEdge) return;
    const newEdge: EdgeDatum = { from: pendingEdge.from, to: pendingEdge.to, type };

    // Immediate local update (optimistic)
    setLocalEdges((prev) => [...prev, newEdge]);

    // Cleanup modal + mode
    setShowAddModal(false);
    setAddEdgeMode(false);
    setPendingEdge(null);

    // // backend call
    // try {
    //   const res = await fetch("/api/dependencies", {
    //     method: "POST",
    //     headers: { "Content-Type": "application/json" },
    //     body: JSON.stringify(newEdge),
    //   });

    //   if (!res.ok) {
    //     // rollback on failure
    //     setLocalEdges((prev) =>
    //       prev.filter((e) => !(e.from === newEdge.from && e.to === newEdge.to && e.type === newEdge.type))
    //     );
    //   }
    // } catch (err) {
    //   setLocalEdges((prev) =>
    //     prev.filter((e) => !(e.from === newEdge.from && e.to === newEdge.to && e.type === newEdge.type))
    //   );
    // }
  };

  const handleCancelAdd = () => {
    setShowAddModal(false);
    setAddEdgeMode(false);
    setPendingEdge(null);
  };

  return (
    <div className="repo-page-wrapper" style={{ display: "flex", gap: 0 }}>
      <GraphCanvas
        key={localEdges.length} // ensures re-render when edges change
        graphData={filteredGraphData}
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
        onConfirm={(type) => handleConfirmAdd(type)}
        onCancel={handleCancelAdd}
      />
    </div>
  );
}
