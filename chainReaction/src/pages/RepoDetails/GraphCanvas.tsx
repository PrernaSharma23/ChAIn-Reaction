// GraphCanvas.tsx
import React, { useEffect, useRef } from "react";
import * as d3 from "d3";
import type { NodeDatum, EdgeDatum } from "./types";
import "./GraphCanvas.scss";
import { getFileName, getRepoName } from "./Utils";

export default function GraphCanvas({
  graphData,
  width = 1000,
  height = 640,
  addEdgeMode = false,
  primaryRepoId,
  secondRepoId,
  onEdgeDragComplete,
  selectedNodeId,
  setSelectedNodeId,
}: {
  graphData: { nodes: NodeDatum[]; edges: EdgeDatum[] } | null | undefined;
  width?: number;
  height?: number;
  addEdgeMode?: boolean;
  primaryRepoId?: string;
  secondRepoId?: string | null;
  onEdgeDragComplete?: (s: string, t: string) => void;
  selectedNodeId?: string | null;
  setSelectedNodeId?: (id: string | null) => void;
}) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!graphData || !graphData.nodes) return;

    const nodes: NodeDatum[] = [...graphData.nodes];
    const edges: EdgeDatum[] = [...(graphData.edges ?? [])];

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();
    svg.style("touch-action", "none");

    const containerWidth = containerRef.current?.clientWidth ?? width;
    const SVG_W = Math.max(700, Math.min(containerWidth - 40, width));
    const SVG_H = height;
    svg.attr("viewBox", `0 0 ${SVG_W} ${SVG_H}`);

    // lookups
    const NodeIdToRepoId = new Map<string, string | undefined>();
    const repoSet = new Set<string>();
    nodes.forEach((n) => {
      if (n.repoId) repoSet.add(n.repoId);
      NodeIdToRepoId.set(n.id, n.repoId);
    });

    const clean = (repo?: string) => (repo ?? "").trim().toLowerCase().replace(/[^a-z0-9]/g, "");

    // prepare links, skip those whose endpoints are not in nodes
    const missingEdges: EdgeDatum[] = [];
    const linksForD3 = edges
      .map((e) => ({ source: e.from, target: e.to, type: e.type }))
      .filter((l) => {
        const hasSrc = NodeIdToRepoId.has(l.source as string);
        const hasTgt = NodeIdToRepoId.has(l.target as string);
        if (!hasSrc || !hasTgt) {
          missingEdges.push({ from: l.source as string, to: l.target as string, type: l.type });
          return false;
        }
        return true;
      });

    if (missingEdges.length > 0) {
      console.warn("[GraphCanvas] skipping edges with missing endpoints:", missingEdges);
    }

    // colors
    const repoColors = d3
      .scaleOrdinal<string>()
      .domain(Array.from(repoSet))
      .range(["#00eaff", "#ff4d8a", "#8a7bff", "#00ffc8"]);
    const interColor = "#37c77f";

    // defs + markers
    const defs = svg.append("defs");

    // marker per repo
    Array.from(repoSet).forEach((repo) => {
      if (!repo) return;
      const key = clean(repo);
      defs
        .append("marker")
        .attr("id", `arrow-${key}`)
        .attr("viewBox", "0 0 10 10")
        .attr("refX", 10)
        .attr("refY", 5)
        .attr("markerWidth", 8)
        .attr("markerHeight", 8)
        .attr("orient", "auto")
        .attr("markerUnits", "userSpaceOnUse")
        .append("path")
        .attr("d", "M 0 0 L 10 5 L 0 10 z")
        .attr("fill", repoColors(repo)!)
        .attr("stroke", "none");
    });

    // inter marker
    defs
      .append("marker")
      .attr("id", "arrow-inter")
      .attr("viewBox", "0 0 10 10")
      .attr("refX", 10)
      .attr("refY", 5)
      .attr("markerWidth", 8)
      .attr("markerHeight", 8)
      .attr("orient", "auto")
      .attr("markerUnits", "userSpaceOnUse")
      .append("path")
      .attr("d", "M 0 0 L 10 5 L 0 10 z")
      .attr("fill", interColor)
      .attr("stroke", "none");

    // HIGHLIGHT (neon yellow) marker + filter
    const highlightColor = "#ffef7a"; // neon yellow
    defs
      .append("marker")
      .attr("id", "arrow-highlight")
      .attr("viewBox", "0 0 10 10")
      .attr("refX", 10)
      .attr("refY", 5)
      .attr("markerWidth", 10)
      .attr("markerHeight", 10)
      .attr("orient", "auto")
      .attr("markerUnits", "userSpaceOnUse")
      .append("path")
      .attr("d", "M 0 0 L 10 5 L 0 10 z")
      .attr("fill", highlightColor)
      .attr("stroke", "none");

    // glow filter for highlight
    const glow = defs
      .append("filter")
      .attr("id", "highlight-glow")
      .attr("x", "-50%")
      .attr("y", "-50%")
      .attr("width", "200%")
      .attr("height", "200%");
    glow.append("feGaussianBlur").attr("stdDeviation", 4).attr("result", "blurOut");
    const merge = glow.append("feMerge");
    merge.append("feMergeNode").attr("in", "blurOut");
    merge.append("feMergeNode").attr("in", "SourceGraphic");

    const gMain = svg.append("g").attr("class", "g-main");

    // overlay for temporary visuals (pointer-events none so it doesn't block nodes)
    const overlay = svg.append("g").attr("class", "overlay-layer").style("pointer-events", "none");

    // legend
    const legend = svg.append("g").attr("transform", "translate(20,20)");
    Array.from(repoSet).forEach((repo, i) => {
      legend.append("circle").attr("cx", 0).attr("cy", i * 22).attr("r", 6).attr("fill", repoColors(repo!));
      legend.append("text").attr("x", 12).attr("y", i * 22 + 4).attr("class", "legend-text").text(getRepoName(repo!)).style("fill", "#ffffff");
    });

    // forces
    const forceX = d3.forceX((d: any) => (d.repoId === nodes[0]?.repoId ? SVG_W * 0.25 : SVG_W * 0.75)).strength(0.09);
    const forceY = d3.forceY(SVG_H / 2).strength(0.04);
    const linkForce = d3.forceLink(linksForD3 as any).id((d: any) => d.id).distance(200);

    const simulation = d3
      .forceSimulation(nodes as any)
      .force("link", linkForce)
      .force("charge", d3.forceManyBody().strength(-270))
      .force("x", forceX)
      .force("y", forceY)
      .force("collide", d3.forceCollide(55))
      .alphaDecay(0.05);

    // link groups
    const linkGroup = gMain
      .append("g")
      .selectAll("g.link")
      .data(linksForD3, (d: any) => `${d.source}__${d.target}`)
      .enter()
      .append("g")
      .attr("class", "link-group");

    const getRepoFrom = (side: any) => {
      if (!side) return undefined;
      if (typeof side === "string") return NodeIdToRepoId.get(side);
      if ((side as any).repoId) return (side as any).repoId;
      if ((side as any).id) return NodeIdToRepoId.get((side as any).id);
      return undefined;
    };

    const linkLines = linkGroup
      .append("line")
      .attr("stroke-width", 2.2)
      .attr("opacity", 0.95)
      .attr("stroke", (d: any) => {
        const sRepo = getRepoFrom(d.source);
        const tRepo = getRepoFrom(d.target);
        return sRepo === tRepo ? repoColors(sRepo!)! : interColor;
      })
      .attr("marker-end", (d: any) => {
        const sRepo = getRepoFrom(d.source);
        const tRepo = getRepoFrom(d.target);
        if (sRepo && tRepo && sRepo === tRepo) return `url(#arrow-${clean(sRepo)})`;
        return "url(#arrow-inter)";
      });

    const edgeLabels = linkGroup
      .append("text")
      .attr("class", "edge-label")
      .style("font-size", "10px")
      .style("font-weight", "500")
      .style("fill", "#ffffff")
      .style("text-shadow", "0 0 3px rgba(0,0,0,0.7)")
      .attr("dy", -6)
      .text((d: any) => d.type ?? "");

    // nodes
    const nodeG = gMain
      .append("g")
      .selectAll("g.node")
      .data(nodes, (d: any) => d.id)
      .enter()
      .append("g")
      .attr("class", "node-group")
      .style("pointer-events", "all");

    nodeG.append("circle").attr("r", 22).attr("stroke-width", 3).attr("fill", "none").attr("stroke", (d: any) => repoColors(d.repoId)!);

    nodeG.append("text").attr("class", "node-label").attr("text-anchor", "middle").attr("dy", 32).text((d: any) => getFileName(d.name) ?? d.id);

   // Debug
    console.log("[GraphCanvas] nodes:", nodes.length, "links (valid):", linksForD3.length, "links (skipped):", missingEdges.length);

    // ---------- Add-edge interaction ----------
    let isDrawing = false;
    let sourceNode: NodeDatum | null = null;
    let hoveredNode: NodeDatum | null = null;
    let tempLine: d3.Selection<SVGLineElement, unknown, null, undefined> | null = null;

    const nx = (n: any) => (typeof n.x === "number" ? n.x : 0);
    const ny = (n: any) => (typeof n.y === "number" ? n.y : 0);

    nodeG.on("mouseover", (event: any, d: NodeDatum) => {
      hoveredNode = d;
    });

    nodeG.on("mouseout", () => {
      hoveredNode = null;
    });

    nodeG.on("mousedown", (event: any, d: NodeDatum) => {
      if (!addEdgeMode) return;
      const allowedReposIds = new Set([primaryRepoId, secondRepoId]);
      if (!allowedReposIds.has(d.repoId ?? "")) return;

       // left-click only
      if (event.button && event.button !== 0) return;

      isDrawing = true;
      sourceNode = d;
      tempLine = overlay
        .append("line")
        .attr("class", "temp-edge")
        .attr("x1", nx(d))
        .attr("y1", ny(d))
        .attr("x2", nx(d))
        .attr("y2", ny(d))
        .attr("stroke-width", 2)
        .attr("stroke-dasharray", "6 6")
        .attr("stroke", "#ffffff")
        .attr("opacity", 0.95)
        .style("pointer-events", "none");

      event.preventDefault();
      event.stopPropagation();
    });

    // click toggles highlight — only when NOT in addEdgeMode
    nodeG.on("click", (event: any, d: NodeDatum) => {
      if (addEdgeMode) return;
      if (selectedNodeId === d.id) {
        setSelectedNodeId?.(null);
      } else {
        setSelectedNodeId?.(d.id);
      }
    });

    const onMove = (event: MouseEvent) => {
      if (!isDrawing || !tempLine) return;
      const pt = d3.pointer(event, svg.node());
      tempLine.attr("x2", pt[0]).attr("y2", pt[1]);
    };

    const onUp = () => {
      if (!isDrawing) return;
      isDrawing = false;
      if (tempLine) {
        tempLine.remove();
        tempLine = null;
      }

      if (!sourceNode || !hoveredNode) {
        sourceNode = null;
        hoveredNode = null;
        return;
      }

      if (sourceNode.id === hoveredNode.id) {
        sourceNode = null;
        hoveredNode = null;
        return;
      }

      if ((sourceNode.repoId ?? "") === (hoveredNode.repoId ?? "")) {
        sourceNode = null;
        hoveredNode = null;
        return;
      }

      const allowedReposIds = new Set([primaryRepoId, secondRepoId]);
      if (!allowedReposIds.has(sourceNode.repoId ?? "") || !allowedReposIds.has(hoveredNode.repoId ?? "")) {
        sourceNode = null;
        hoveredNode = null;
        return;
      }

      onEdgeDragComplete?.(sourceNode.id, hoveredNode.id);

      sourceNode = null;
      hoveredNode = null;
    };

    d3.select(window).on("mousemove.dragcreate", onMove).on("mouseup.dragcreate", onUp);

    // restart simulation to ensure newly added links settle into place
    simulation.alpha(0.8).restart();

    // TICK: update positions and apply highlight only to connected edges/nodes (no fading)
    simulation.on("tick", () => {
      // positions
      linkLines
        .attr("x1", (d: any) => (d.source && typeof d.source.x === "number" ? d.source.x : 0))
        .attr("y1", (d: any) => (d.source && typeof d.source.y === "number" ? d.source.y : 0))
        .attr("x2", (d: any) => (d.target && typeof d.target.x === "number" ? d.target.x : 0))
        .attr("y2", (d: any) => (d.target && typeof d.target.y === "number" ? d.target.y : 0));

      // highlight logic: only change stroke & apply glow for connected edges; otherwise keep original stroke
      linkLines.each(function (d: any) {
        const elem = d3.select(this);
        const sId = (d.source as any).id ?? d.source;
        const tId = (d.target as any).id ?? d.target;

        if (selectedNodeId && (sId === selectedNodeId || tId === selectedNodeId)) {
          // highlight edge
          elem
            .attr("stroke", highlightColor)
            .attr("stroke-width", 4)
            .attr("filter", "url(#highlight-glow)")
            .attr("marker-end", "url(#arrow-highlight)");
        } else {
          // restore default edge color and marker (repo or inter)
          const sRepo = getRepoFrom(d.source);
          const tRepo = getRepoFrom(d.target);
          const baseColor = sRepo === tRepo ? repoColors(sRepo!)! : interColor;
          const baseMarker = sRepo && tRepo && sRepo === tRepo ? `url(#arrow-${clean(sRepo)})` : "url(#arrow-inter)";

          elem
            .attr("stroke", baseColor)
            .attr("stroke-width", 2.2)
            .attr("filter", null)
            .attr("marker-end", baseMarker);
        }
      });

      // nodes: if selected or connected, highlight those nodes' strokes; do not dim others
      nodeG.selectAll("circle").each(function (d: any) {
        const el = d3.select(this);
        if (!selectedNodeId) {
          // restore repo stroke
          el.attr("stroke", repoColors(d.repoId!)!).attr("stroke-width", 3).attr("filter", null);
          return;
        }

        // determine if node is connected to selectedNodeId
        const connected = linksForD3.some((l: any) => {
          const s = l.source as string;
          const t = l.target as string;
          return (s === selectedNodeId && (d.id === t)) || (t === selectedNodeId && (d.id === s));
        });

        if (d.id === selectedNodeId) {
          // selected node: strong highlight
          el.attr("stroke", highlightColor).attr("stroke-width", 5).attr("filter", "url(#highlight-glow)");
        } else if (connected) {
          // connected node: highlight slightly
          el.attr("stroke", highlightColor).attr("stroke-width", 4).attr("filter", "url(#highlight-glow)");
        } else {
          // unrelated node: keep original repo color
          el.attr("stroke", repoColors(d.repoId!)!).attr("stroke-width", 3).attr("filter", null);
        }
      });

      // position labels and groups
      linkGroup.selectAll("text").attr("x", (d: any) => ((d.source?.x ?? 0) + (d.target?.x ?? 0)) / 2).attr("y", (d: any) => ((d.source?.y ?? 0) + (d.target?.y ?? 0)) / 2);

      nodeG.attr("transform", (d: any) => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

    // cleanup
    return () => {
      simulation.stop();
      d3.select(window).on("mousemove.dragcreate", null).on("mouseup.dragcreate", null);
    };
  }, [graphData, width, height, addEdgeMode, primaryRepoId, secondRepoId, onEdgeDragComplete, selectedNodeId, setSelectedNodeId]);

  return (
    <div className="repo-details-outer" ref={containerRef}>
      <div className="repo-details-header">
        <h2>Dependency Graph</h2>
        <p className="subtitle">Interactive dependency visualization</p>
      </div>

      <div className="repo-graph">
        <svg ref={svgRef} className="repo-svg" />
      </div>
    </div>
  );
}
