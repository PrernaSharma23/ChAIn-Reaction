// RepoPickerModal.tsx
import React from "react";
import "./RepoPickerModal.scss";

interface RepoPickerModalProps {
  isOpen: boolean;
  options: string[];
  onSelect: (repo: string) => void;
  onClose: () => void;
}

export default function RepoPickerModal({
  isOpen,
  options,
  onSelect,
  onClose,
}: RepoPickerModalProps) {
  if (!isOpen) return null;

  const [temp, setTemp] = React.useState("");

  // reset local selection when modal opens
  React.useEffect(() => {
    setTemp("");
  }, [isOpen]);

  return (
    <div className="repo-modal-overlay">
      <div className="repo-modal">
        <div className="modal-header">
          <h3>Select second repo</h3>
        </div>

        <div className="modal-body">
          <label className="modal-label">Available repos</label>

          <select
            className="repo-select"
            value={temp}
            onChange={(e) => setTemp(e.target.value)}
          >
            <option value="">-- Choose repo --</option>
            {options.map((repo) => (
              <option key={repo} value={repo}>
                {repo}
              </option>
            ))}
          </select>
        </div>

        <div className="modal-actions">
          <button className="btn ghost" onClick={onClose}>
            Cancel
          </button>

          <button
            className="btn primary"
            disabled={!temp}
            onClick={() => {
              onSelect(temp);
              onClose();
            }}
          >
            OK
          </button>
        </div>
      </div>
    </div>
  );
}
