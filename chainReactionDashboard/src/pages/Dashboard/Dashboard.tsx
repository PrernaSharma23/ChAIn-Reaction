// src/pages/dashboard/Dashboard.tsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Dashboard.scss";
import { getRepoMap } from "../RepoDetails/Utils";
import { map } from "lodash";

export default function Dashboard() {
  const navigate = useNavigate();
  const [selectedRepoId, setSelectedRepoId] = useState("");

  const repoMap = getRepoMap();
  const options = map(repoMap, (name, id) => ({ id, name }));  

  const handleSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const repoId = e.target.value;
    setSelectedRepoId(repoId);

    if (repoId) navigate(`/repo-details/${repoId}`);
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-panel">

        {/* LEFT SIDE */}
        <div className="left-section">
          <h1 className="dashboard-title">System Dependency Explorer</h1>

          <p className="dashboard-desc">
            Explore intra-repo, inter-repo and multi-level dependencies visually
            and interactively.
          </p>

          <div className="dropdown-wrapper">
            <label>Select a Repository</label>

            <select
              className="dashboard-dropdown large"
              value={selectedRepoId}
              onChange={handleSelect}
            >
              <option value="">-- Select Repository --</option>

              {options.map((opt) => (
              <option key={opt.id} value={opt.id}>
                {opt.name}
              </option>
            ))}
            </select>
          </div>
        </div>

        {/* RIGHT SIDE SVG */}
        <div className="right-graphic">
          <svg viewBox="0 0 200 200" className="illustration">
            <circle cx="100" cy="100" r="80" fill="#1b3450" />
            <circle cx="100" cy="100" r="55" fill="#274766" />
            <circle cx="100" cy="100" r="30" fill="#3da9fc" />
          </svg>
        </div>
      </div>
    </div>
  );
}
