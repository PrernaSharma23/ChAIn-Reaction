// SidePanel.tsx (small changes: addEdgeMode toggle UI)
import React from "react";
import RepoPickerModal from "./RepoPickerModal";
import "./SidePanel.scss";

export default function SidePanel({
  repoName,
  viewType,
  setViewType,
  secondRepo,
  setSecondRepo,
  showRepoPicker,
  setShowRepoPicker,
  allRepos,
  addEdgeMode,
  setAddEdgeMode,
}: {
  repoName: string;
  viewType: "intra" | "inter";
  setViewType: (v: "intra" | "inter") => void;
  secondRepo: string | null;
  setSecondRepo: (r: string | null) => void;
  showRepoPicker: boolean;
  setShowRepoPicker: (b: boolean) => void;
  allRepos: string[];
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
          <div className="value">{repoName || "-"}</div>
        </div>

        <div className="section">
          <div className="label">View Type</div>
          <div className="controls">
            <button
              className={`seg ${viewType === "intra" ? "active" : ""}`}
              onClick={() => {
                setViewType("intra");
                setSecondRepo(null);
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
            <div className="value">{secondRepo ?? <em>Not selected</em>}</div>

            <div className="controls-row">
              <button className="ghost" onClick={() => setShowRepoPicker(true)}>
                Choose Second Repo
              </button>

              {/* Add dependency button only visible in inter view */}
              <button
                className={`primary ${addEdgeMode ? "active-mode" : ""}`}
                disabled={!secondRepo}
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
        options={allRepos.filter((r) => r !== repoName)}
        onSelect={(r) => {
          setSecondRepo(r);
          setShowRepoPicker(false);
        }}
        onClose={() => setShowRepoPicker(false)}
      />
    </aside>
  );
}
