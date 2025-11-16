// SidePanel.tsx (small changes: addEdgeMode toggle UI)
import React from "react";
import RepoPickerModal from "./RepoPickerModal";
import "./SidePanel.scss";
import { getRepoName } from "./Utils";

export default function SidePanel({
  primaryRepoId,
  viewType,
  setViewType,
  secondRepoId,
  setSecondRepoId,
  showRepoPicker,
  setShowRepoPicker,
  allReposIds,
  addEdgeMode,
  setAddEdgeMode,
}: {
  primaryRepoId: string;
  viewType: "intra" | "inter";
  setViewType: (v: "intra" | "inter") => void;
  secondRepoId: string | null;
  setSecondRepoId: (r: string | null) => void;
  showRepoPicker: boolean;
  setShowRepoPicker: (b: boolean) => void;
  allReposIds: string[];
  addEdgeMode: boolean;
  setAddEdgeMode: (b: boolean) => void;
}) {
  const onInterClick = () => {
    setViewType("inter");
    setShowRepoPicker(true);
  };

  return (
    <aside className="side-panel">
      <div className="panel-inner">
        <div className="panel-head">
          <div className="title">Repo Details</div>
          <div className="subtitle">Inspect dependencies</div>
        </div>

        <div className="section">
          <div className="label">Primary Repo</div>
          <div className="value">{getRepoName(primaryRepoId) || "-"}</div>
        </div>

        <div className="section">
          <div className="label">View Type</div>
          <div className="controls">
            <button
              className={`seg ${viewType === "intra" ? "active" : ""}`}
              onClick={() => {
                setViewType("intra");
                setSecondRepoId(null);
                setAddEdgeMode(false);
              }}
            >
              Intra Repo
            </button>

            <button
              className={`seg ${viewType === "inter" ? "active" : ""}`}
              onClick={onInterClick}
            >
              Inter Repo
            </button>
          </div>
        </div>

        {viewType === "inter" && (
          <div className="section">
            <div className="label">Second Repo</div>
            <div className="value">{getRepoName(secondRepoId ?? '') ?? <em>Not selected</em>}</div>

            <div className="controls-row">
              <button className="ghost" onClick={() => setShowRepoPicker(true)}>
                Choose Second Repo
              </button>

              {/* Add dependency button only visible in inter view */}
              <button
                className={`primary ${addEdgeMode ? "active-mode" : ""}`}
                disabled={!secondRepoId}
                onClick={() => setAddEdgeMode(!addEdgeMode)}
                title={addEdgeMode ? "Cancel add dependency" : "Add dependency (drag from source to target)"}
              >
                {addEdgeMode ? "Cancel Add" : "Add Dependency"}
              </button>
            </div>

            {addEdgeMode && (
              <div style={{ marginTop: 8, color: "#bcd5ea", fontSize: 12 }}>
                Drag from source node to target node. Only cross-repo edges allowed.
              </div>
            )}
          </div>
        )}

        <div className="spacer" />
      </div>

      <RepoPickerModal
        isOpen={showRepoPicker}
        options={allReposIds
          .filter((r) => r !== primaryRepoId)
          .map((id) => ({ id, name: getRepoName(id) }))}
        onSelect={(r) => {
          setSecondRepoId(r);
          setShowRepoPicker(false);
        }}
        onClose={() => setShowRepoPicker(false)}
      />
    </aside>
  );
}
