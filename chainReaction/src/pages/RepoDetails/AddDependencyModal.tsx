import React, { useMemo, useState, useEffect } from "react";
import _ from "lodash";
import Select, { components } from "react-select";
import "./AddDependencyModal.scss";
import type { NodeDatum } from "./types";
import { getRepoName, getFileName } from "./Utils";

type Option = { label: string; value: string; meta?: string };

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
  onConfirm: (type: string, from?: string, to?: string) => void;
  onCancel: () => void;
}) {
  const sourceNode = useMemo(
    () => nodes.find((n) => n.id === sourceId) ?? null,
    [nodes, sourceId]
  );

  const targetNode = useMemo(
    () => nodes.find((n) => n.id === targetId) ?? null,
    [nodes, targetId]
  );

  const repoOptions = useMemo(() => {
    const ids = _.uniq(
      [sourceNode?.repoId ?? null, targetNode?.repoId ?? null].filter(Boolean)
    ) as string[];

    return ids.map((id) => ({
      label: getRepoName(id),
      value: id,
      meta: id,
    }));
  }, [sourceNode, targetNode]);

  const [selectedSourceRepo, setSelectedSourceRepo] = useState<Option | null>(null);
  const [selectedTargetRepo, setSelectedTargetRepo] = useState<Option | null>(null);
  const [selectedSourceNode, setSelectedSourceNode] = useState<Option | null>(null);
  const [selectedTargetNode, setSelectedTargetNode] = useState<Option | null>(null);
  const [type, setType] = useState<string | null>(null);

  const sourceRepoNodes = useMemo(
    () =>
      nodes.filter(
        (n) =>
          n.repoId ===
          (selectedSourceRepo?.value ?? sourceNode?.repoId ?? undefined)
      ),
    [nodes, selectedSourceRepo, sourceNode]
  );

  const targetRepoNodes = useMemo(
    () =>
      nodes.filter(
        (n) =>
          n.repoId ===
          (selectedTargetRepo?.value ?? targetNode?.repoId ?? undefined)
      ),
    [nodes, selectedTargetRepo, targetNode]
  );

  const mapNodeToOption = (n: NodeDatum): Option => ({
    label: getFileName(n.id ?? ""),
    value: n.id ?? "",
    meta: n.id ?? "",
  });

  const sourceNodeOptions = useMemo(
    () => sourceRepoNodes.map(mapNodeToOption),
    [sourceRepoNodes]
  );

  const targetNodeOptions = useMemo(
    () => targetRepoNodes.map(mapNodeToOption),
    [targetRepoNodes]
  );

  useEffect(() => {
    if (!isOpen) return;

    const srcRepo =
      repoOptions.find((r) => r.value === sourceNode?.repoId) ??
      repoOptions[0] ??
      null;

    const tgtRepo =
      repoOptions.find((r) => r.value === targetNode?.repoId) ??
      repoOptions[repoOptions.length - 1] ??
      null;

    setSelectedSourceRepo(srcRepo);
    setSelectedTargetRepo(tgtRepo);

    const srcNodeOpt = sourceNode ? mapNodeToOption(sourceNode) : null;
    const tgtNodeOpt = targetNode ? mapNodeToOption(targetNode) : null;

    const initialSrcNode =
      srcNodeOpt && srcRepo && sourceNode?.repoId === srcRepo.value
        ? srcNodeOpt
        : sourceNodeOptions[0] ?? srcNodeOpt ?? null;

    const initialTgtNode =
      tgtNodeOpt && tgtRepo && targetNode?.repoId === tgtRepo.value
        ? tgtNodeOpt
        : targetNodeOptions[0] ?? tgtNodeOpt ?? null;

    setSelectedSourceNode(initialSrcNode);
    setSelectedTargetNode(initialTgtNode);

    setType(null);
  }, [isOpen, sourceId, targetId, nodes]);

  useEffect(() => {
    if (
      selectedSourceNode &&
      !sourceRepoNodes.find((n) => n.id === selectedSourceNode.value)
    ) {
      setSelectedSourceNode(sourceNodeOptions[0] ?? null);
    }
  }, [selectedSourceRepo, sourceRepoNodes]);

  useEffect(() => {
    if (
      selectedTargetNode &&
      !targetRepoNodes.find((n) => n.id === selectedTargetNode.value)
    ) {
      setSelectedTargetNode(targetNodeOptions[0] ?? null);
    }
  }, [selectedTargetRepo, targetRepoNodes]);

  if (!isOpen) return null;

  // custom option
  const OptionComp = (props: any) => (
    <components.Option {...props}>
      <div className="adm-option" title={props.data.meta ?? props.data.label}>
        {props.data.label}
      </div>
    </components.Option>
  );

  const SingleValueComp = (props: any) => (
    <components.SingleValue
      {...props}
      title={props.data.meta ?? props.data.label}
    >
      <div className="adm-single-value">{props.children}</div>
    </components.SingleValue>
  );

  return (
    <div className="adm-overlay">
      <div className="adm-card">
        <h3 className="adm-title">Create Dependency</h3>

        <div className="adm-row">
          {/* SOURCE */}
          <div className="adm-col">
            <label className="adm-label">Source Repo</label>
            <div className="adm-select-wrapper">
              <Select
                classNamePrefix="react-select"
                components={{ Option: OptionComp, SingleValue: SingleValueComp }}
                options={repoOptions}
                value={selectedSourceRepo}
                onChange={(v) => setSelectedSourceRepo(v as Option)}
                isSearchable
                placeholder="Select repo..."
                menuPlacement="auto"
              />
            </div>

            <label className="adm-label">Source Node</label>
            <div className="adm-select-wrapper">
              <Select
                classNamePrefix="react-select"
                components={{ Option: OptionComp, SingleValue: SingleValueComp }}
                options={sourceNodeOptions}
                value={selectedSourceNode}
                onChange={(v) => setSelectedSourceNode(v as Option)}
                isSearchable
                placeholder="Select node..."
                noOptionsMessage={() => "No nodes"}
              />
            </div>

            <div className="adm-node-details">
              <label className="adm-node-details-label">Source Node Details</label>
              <div
                className="adm-node-details-value"
                title={selectedSourceNode?.meta ?? selectedSourceNode?.label ?? ""}
              >
                {selectedSourceNode?.label ?? "—"}
              </div>
            </div>
          </div>

          {/* TARGET */}
          <div className="adm-col">
            <label className="adm-label">Target Repo</label>
            <div className="adm-select-wrapper">
              <Select
                classNamePrefix="react-select"
                components={{ Option: OptionComp, SingleValue: SingleValueComp }}
                options={repoOptions}
                value={selectedTargetRepo}
                onChange={(v) => setSelectedTargetRepo(v as Option)}
                isSearchable
                placeholder="Select repo..."
                menuPlacement="auto"
              />
            </div>

            <label className="adm-label">Target Node</label>
            <div className="adm-select-wrapper">
              <Select
                classNamePrefix="react-select"
                components={{ Option: OptionComp, SingleValue: SingleValueComp }}
                options={targetNodeOptions}
                value={selectedTargetNode}
                onChange={(v) => setSelectedTargetNode(v as Option)}
                isSearchable
                placeholder="Select node..."
                noOptionsMessage={() => "No nodes"}
              />
            </div>

            <div className="adm-node-details">
              <label className="adm-node-details-label">Target Node Details</label>
              <div
                className="adm-node-details-value"
                title={selectedTargetNode?.meta ?? selectedTargetNode?.label ?? ""}
              >
                {selectedTargetNode?.label ?? "—"}
              </div>
            </div>
          </div>
        </div>

        <div className="adm-deps">
          <label className="adm-label">Dependency Type</label>
          <div className="adm-deps-list">
            {["CONTAINS", "DEPENDS_ON", "WRITES_TO", "READS_FROM"].map((t) => (
              <label key={t}>
                <input
                  type="radio"
                  name="dep"
                  checked={type === t}
                  onChange={() => setType(t)}
                />{" "}
                {t}
              </label>
            ))}
          </div>
        </div>

        <div className="adm-actions">
          <button className="adm-btn-cancel" onClick={onCancel}>
            Cancel
          </button>

          <button
            className="adm-btn-confirm"
            disabled={!type}
            onClick={() =>
              type &&
              onConfirm(
                type,
                selectedSourceNode?.value ?? sourceId ?? undefined,
                selectedTargetNode?.value ?? targetId ?? undefined
              )
            }
          >
            Create Dependency
          </button>
        </div>
      </div>
    </div>
  );
}
