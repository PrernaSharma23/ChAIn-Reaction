// RepoPickerModal.tsx
import React from "react";
import "./RepoPickerModal.scss";

interface RepoOption {
  id: string;
  name: string;
}

interface RepoPickerModalProps {
  isOpen: boolean;
  options: RepoOption[];
  onSelect: (repoId: string) => void;
  onClose: () => void;
}

export default function RepoPickerModal({
  isOpen,
  options,
  onSelect,
  onClose,
}: RepoPickerModalProps) {

  const [temp, setTemp] = React.useState("");

  // reset local selection when modal opens
  React.useEffect(() => {
    setTemp("");
  }, [isOpen]);

  if (!isOpen) return null;

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
            {options.map((opt) => (
              <option key={opt.id} value={opt.id}>
                {opt.name}
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
              onSelect(temp); // pass ID
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
