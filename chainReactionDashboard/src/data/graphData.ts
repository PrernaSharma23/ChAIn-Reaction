// small mock graph, circular node appearance is handled by custom node type
export interface GraphNode {
  id: string;
  label: string;
  // optional: initial position (will be overwritten by D3 once laid out)
  x?: number;
  y?: number;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
}

export const nodesMock: GraphNode[] = [
  { id: "A", label: "service-A" },
  { id: "B", label: "service-B" },
  { id: "C", label: "service-C" },
  { id: "D", label: "service-D" },
  { id: "E", label: "service-E" }
];

export const edgesMock: GraphEdge[] = [
  { id: "eA-B", source: "A", target: "B" },
  { id: "eA-C", source: "A", target: "C" },
  { id: "eB-D", source: "B", target: "D" },
  { id: "eC-D", source: "C", target: "D" },
  { id: "eD-E", source: "D", target: "E" }
];
