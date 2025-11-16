// GraphCanvas.tsx — defensive, restart-on-update edition with node click highlighting
import React, { useEffect, useRef } from "react";
import * as d3 from "d3";
import type { NodeDatum, EdgeDatum } from "./types";
import "./GraphCanvas.scss";

export default function GraphCanvas({
  graphData,
  width = 1000,
  height = 640,
  addEdgeMode = false,
  primaryRepo,
  secondRepo,
  onEdgeDragComplete,
  selectedNodeId,
  setSelectedNodeId,
}: {
  graphData: { nodes: NodeDatum[]; edges: EdgeDatum[] } | null | undefined;
  width?: number;
  height?: number;
  addEdgeMode?: boolean;
  primaryRepo?: string;
  secondRepo?: string | null;
  onEdgeDragComplete?: (s: string, t: string) => void;
  selectedNodeId?: string | null;
  setSelectedNodeId?: (id: string | null) => void;
}) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    // Basic guard
    if (!graphData || !graphData.nodes) return;

    const nodes: NodeDatum[] = [...graphData.nodes];
    const edges: EdgeDatum[] = [...(graphData.edges ?? [])];

    // cleanup and base svg
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();
    svg.style("touch-action", "none");

    const containerWidth = containerRef.current?.clientWidth ?? width;
    const SVG_W = Math.max(700, Math.min(containerWidth - 40, width));
    const SVG_H = height;
    svg.attr("viewBox", `0 0 ${SVG_W} ${SVG_H}`);

    // maps for lookups
    const idToRepo = new Map<string, string | undefined>();
    const repoSet = new Set<string>();
    nodes.forEach((n) => {
      if (n.repo) repoSet.add(n.repo);
      idToRepo.set(n.id, n.repo);
    });

    const clean = (repo?: string) =>
      (repo ?? "").trim().toLowerCase().replace(/[^a-z0-9]/g, "");

    // Build linksForD3 but FILTER invalid endpoints (defensive)
    const missingEdges: EdgeDatum[] = [];
    const linksForD3 = edges
      .map((e) => ({ source: e.from, target: e.to, type: e.type }))
      .filter((l) => {
        const hasSrc = idToRepo.has(l.source as string);
        const hasTgt = idToRepo.has(l.target as string);
        if (!hasSrc || !hasTgt) {
          missingEdges.push({ from: l.source as string, to: l.target as string, type: l.type });
          return false;
        }
        return true;
      });

    if (missingEdges.length > 0) {
      console.warn("[GraphCanvas] Skipping edges whose endpoints are missing from current nodes:", missingEdges);
    }

    // colors
    const repoColors = d3
      .scaleOrdinal<string>()
      .domain(Array.from(repoSet))
      .range(["#00eaff", "#ff4d8a", "#8a7bff", "#00ffc8"]);
    const interColor = "#37c77f";

    // defs / markers
    const defs = svg.append("defs");
    Array.from(repoSet).forEach((repo) => {
      if (!repo) return;
      defs
        .append("marker")
        .attr("id", `arrow-${clean(repo)}`)
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

    // --- glow filter for highlighting selected edges ---
    const glow = defs
      .append("filter")
      .attr("id", "edge-glow")
      .attr("x", "-50%")
      .attr("y", "-50%")
      .attr("width", "200%")
      .attr("height", "200%");
    glow.append("feGaussianBlur").attr("stdDeviation", 4).attr("result", "coloredBlur");
    const feMerge = glow.append("feMerge");
    feMerge.append("feMergeNode").attr("in", "coloredBlur");
    feMerge.append("feMergeNode").attr("in", "SourceGraphic");

    const gMain = svg.append("g").attr("class", "g-main");

    // overlay for temporary visuals (pointer-events none so it doesn't block nodes)
    const overlay = svg.append("g").attr("class", "overlay-layer").style("pointer-events", "none");

    // legend (optional)
    const legend = svg.append("g").attr("transform", "translate(20,20)");
    Array.from(repoSet).forEach((repo, i) => {
      legend.append("circle").attr("cx", 0).attr("cy", i * 22).attr("r", 6).attr("fill", repoColors(repo!));
      legend.append("text").attr("x", 12).attr("y", i * 22 + 4).attr("class", "legend-text").text(repo!).style("fill", "#ffffff");
    });

    // forces
    const forceX = d3.forceX((d: any) => (d.repo === nodes[0]?.repo ? SVG_W * 0.25 : SVG_W * 0.75)).strength(0.09);
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

    // links group with a key to help D3 reconcile (source-target string)
    const linkGroup = gMain
      .append("g")
      .selectAll("g.link")
      .data(linksForD3, (d: any) => `${d.source}__${d.target}`)
      .enter()
      .append("g")
      .attr("class", "link-group");

    const getRepoFrom = (side: any) => {
      if (!side) return undefined;
      if (typeof side === "string") return idToRepo.get(side);
      if ((side as any).repo) return (side as any).repo;
      if ((side as any).id) return idToRepo.get((side as any).id);
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

    nodeG.append("circle").attr("r", 22).attr("stroke-width", 3).attr("fill", "none").attr("stroke", (d: any) => repoColors(d.repo!)!);

    nodeG.append("text").attr("class", "node-label").attr("text-anchor", "middle").attr("dy", 32).text((d: any) => d.name ?? d.id);

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
      const allowedRepos = new Set([primaryRepo, secondRepo]);
      if (!allowedRepos.has(d.repo ?? "")) return;

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

    // --- NEW: click handler for selection (only when NOT in addEdgeMode) ---
    nodeG.on("click", (event: any, d: NodeDatum) => {
      // if addEdgeMode active, clicks are used for edge-drag flow — do not toggle selection
      if (addEdgeMode) return;

      // toggle selection
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

      if ((sourceNode.repo ?? "") === (hoveredNode.repo ?? "")) {
        sourceNode = null;
        hoveredNode = null;
        return;
      }

      const allowedRepos = new Set([primaryRepo, secondRepo]);
      if (!allowedRepos.has(sourceNode.repo ?? "") || !allowedRepos.has(hoveredNode.repo ?? "")) {
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

    // tick: update positions and highlight logic based on selectedNodeId
    simulation.on("tick", () => {
      linkLines
        .attr("x1", (d: any) => (d.source && typeof d.source.x === "number" ? d.source.x : 0))
        .attr("y1", (d: any) => (d.source && typeof d.source.y === "number" ? d.source.y : 0))
        .attr("x2", (d: any) => (d.target && typeof d.target.x === "number" ? d.target.x : 0))
        .attr("y2", (d: any) => (d.target && typeof d.target.y === "number" ? d.target.y : 0));

      // Highlighting logic:
      linkLines
        .attr("stroke-opacity", (d: any) => {
          if (!selectedNodeId) return 0.95;
          const sId = (d.source as any).id ?? d.source;
          const tId = (d.target as any).id ?? d.target;
          return sId === selectedNodeId || tId === selectedNodeId ? 1 : 0.12;
        })
        .attr("stroke-width", (d: any) => {
          if (!selectedNodeId) return 2.2;
          const sId = (d.source as any).id ?? d.source;
          const tId = (d.target as any).id ?? d.target;
          return sId === selectedNodeId || tId === selectedNodeId ? 3.2 : 1;
        })
        .attr("filter", (d: any) => {
          if (!selectedNodeId) return null;
          const sId = (d.source as any).id ?? d.source;
          const tId = (d.target as any).id ?? d.target;
          return sId === selectedNodeId || tId === selectedNodeId ? "url(#edge-glow)" : null;
        });

      // node circle highlighting & opacity
      nodeG.selectAll("circle")
        .attr("stroke-width", (d: any) => {
          if (!selectedNodeId) return 3;
          return d.id === selectedNodeId ? 5 : 2;
        })
        .attr("opacity", (d: any) => {
          if (!selectedNodeId) return 1;
          return d.id === selectedNodeId ? 1 : 0.45;
        });

      // optionally adjust node labels opacity
      nodeG.selectAll("text.node-label")
        .attr("opacity", (d: any) => {
          if (!selectedNodeId) return 1;
          return d.id === selectedNodeId ? 1 : 0.6;
        });

      linkGroup.selectAll("text").attr("x", (d: any) => ((d.source?.x ?? 0) + (d.target?.x ?? 0)) / 2).attr("y", (d: any) => ((d.source?.y ?? 0) + (d.target?.y ?? 0)) / 2);

      nodeG.attr("transform", (d: any) => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

    // cleanup
    return () => {
      simulation.stop();
      d3.select(window).on("mousemove.dragcreate", null).on("mouseup.dragcreate", null);
    };
  }, [graphData, width, height, addEdgeMode, primaryRepo, secondRepo, onEdgeDragComplete, selectedNodeId, setSelectedNodeId]);

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
