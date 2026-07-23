/** Relationship graph transforms (KC-007). */

export type StudioGraphNodeType =
  | "people"
  | "org"
  | "department"
  | "evidence"
  | "policy"
  | "contract"
  | "budget"
  | "finding"
  | "report"
  | "timeline"
  | "investigation";

export interface StudioGraphNode {
  id: string;
  type: StudioGraphNodeType;
  label: string;
  metadata?: Record<string, unknown>;
}

export interface StudioGraphEdge {
  id: string;
  sourceId: string;
  targetId: string;
  label: string;
  confidence?: number | null;
  citationIds?: string[];
  metadata?: Record<string, unknown>;
}

export interface StudioGraph {
  nodes: StudioGraphNode[];
  edges: StudioGraphEdge[];
}

export interface StudioGraphFilter {
  types?: StudioGraphNodeType[];
  q?: string;
  minConfidence?: number;
}

export interface StudioGraphNeighborhood {
  centerId: string;
  nodeIds: string[];
  edgeIds: string[];
  nodes: StudioGraphNode[];
  edges: StudioGraphEdge[];
}

export function buildRelationshipGraph(
  nodes: StudioGraphNode[],
  edges: StudioGraphEdge[],
): StudioGraph {
  const nodeIds = new Set(nodes.map((n) => n.id));
  const validEdges = edges.filter(
    (e) => nodeIds.has(e.sourceId) && nodeIds.has(e.targetId) && e.sourceId !== e.targetId,
  );
  return {
    nodes: [...nodes],
    edges: validEdges,
  };
}

export function filterGraph(graph: StudioGraph, filter: StudioGraphFilter = {}): StudioGraph {
  const types = filter.types?.length ? new Set(filter.types) : null;
  const q = filter.q?.trim().toLowerCase();
  const minConfidence = filter.minConfidence;

  let nodes = graph.nodes;
  if (types) {
    nodes = nodes.filter((n) => types.has(n.type));
  }
  if (q) {
    nodes = nodes.filter((n) => n.label.toLowerCase().includes(q));
  }
  const nodeIds = new Set(nodes.map((n) => n.id));

  let edges = graph.edges.filter((e) => nodeIds.has(e.sourceId) && nodeIds.has(e.targetId));
  if (minConfidence != null && Number.isFinite(minConfidence)) {
    edges = edges.filter((e) => (e.confidence ?? 0) >= minConfidence);
  }

  return { nodes, edges };
}

export function highlightNeighborhood(
  graph: StudioGraph,
  nodeId: string,
  depth = 1,
): StudioGraphNeighborhood {
  const adjacency = new Map<string, Set<string>>();
  const edgeByNode = new Map<string, StudioGraphEdge[]>();

  for (const edge of graph.edges) {
    if (!adjacency.has(edge.sourceId)) adjacency.set(edge.sourceId, new Set());
    if (!adjacency.has(edge.targetId)) adjacency.set(edge.targetId, new Set());
    adjacency.get(edge.sourceId)!.add(edge.targetId);
    adjacency.get(edge.targetId)!.add(edge.sourceId);

    if (!edgeByNode.has(edge.sourceId)) edgeByNode.set(edge.sourceId, []);
    if (!edgeByNode.has(edge.targetId)) edgeByNode.set(edge.targetId, []);
    edgeByNode.get(edge.sourceId)!.push(edge);
    edgeByNode.get(edge.targetId)!.push(edge);
  }

  const visited = new Set<string>([nodeId]);
  let frontier = new Set<string>([nodeId]);

  for (let d = 0; d < depth; d++) {
    const next = new Set<string>();
    for (const id of frontier) {
      for (const neighbor of adjacency.get(id) ?? []) {
        if (!visited.has(neighbor)) {
          visited.add(neighbor);
          next.add(neighbor);
        }
      }
    }
    frontier = next;
  }

  const nodeIds = [...visited];
  const nodes = graph.nodes.filter((n) => visited.has(n.id));
  const edgeIds = new Set<string>();
  const edges: StudioGraphEdge[] = [];

  for (const id of nodeIds) {
    for (const edge of edgeByNode.get(id) ?? []) {
      if (visited.has(edge.sourceId) && visited.has(edge.targetId) && !edgeIds.has(edge.id)) {
        edgeIds.add(edge.id);
        edges.push(edge);
      }
    }
  }

  return {
    centerId: nodeId,
    nodeIds,
    edgeIds: [...edgeIds],
    nodes,
    edges,
  };
}

export function attachConfidenceOverlay(
  edges: StudioGraphEdge[],
  confidenceByEdgeId: Record<string, number>,
): StudioGraphEdge[] {
  return edges.map((edge) => ({
    ...edge,
    confidence:
      confidenceByEdgeId[edge.id] != null && Number.isFinite(confidenceByEdgeId[edge.id])
        ? confidenceByEdgeId[edge.id]
        : edge.confidence ?? null,
    metadata: {
      ...(edge.metadata ?? {}),
      confidenceOverlay: true,
    },
  }));
}

export function attachCitationOverlay(
  edges: StudioGraphEdge[],
  citationsByEdgeId: Record<string, string[]>,
): StudioGraphEdge[] {
  return edges.map((edge) => ({
    ...edge,
    citationIds: citationsByEdgeId[edge.id] ?? edge.citationIds ?? [],
    metadata: {
      ...(edge.metadata ?? {}),
      citationOverlay: true,
    },
  }));
}
