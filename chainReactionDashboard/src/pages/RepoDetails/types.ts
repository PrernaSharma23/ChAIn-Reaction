// types.ts
export type NodeDatum = {
  id: string;
  repoId?: string;
  type?: string;
  x?: number;
  y?: number;
};

export type EdgeDatum = {
  from: string;
  to: string;
  type?: string;
};
