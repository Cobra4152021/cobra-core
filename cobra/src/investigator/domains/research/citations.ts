/** Citation explorer graph (KC-009). */

export type CitationNodeKind = "papers" | "books" | "reports" | "web" | "vault" | "cke";

export interface CitationNode {
  id: string;
  kind: CitationNodeKind;
  label: string;
  citationId: string | null;
}

export interface CitationLink {
  from: string;
  to: string;
  relation: "cites" | "derived_from" | "related" | "contradicts";
}

export interface CitationGraph {
  nodes: CitationNode[];
  links: CitationLink[];
}

export interface CitationNeighborhood {
  centerId: string;
  nodes: CitationNode[];
  links: CitationLink[];
  depth: number;
}

export function buildCitationGraph(links: {
  nodes: CitationNode[];
  links: CitationLink[];
}): CitationGraph {
  return {
    nodes: links.nodes.map((n) => ({ ...n })),
    links: links.links.map((l) => ({ ...l })),
  };
}

export function exploreNeighborhood(
  graph: CitationGraph,
  nodeId: string,
  depth = 1,
): CitationNeighborhood {
  const nodeMap = new Map(graph.nodes.map((n) => [n.id, n]));
  const center = nodeMap.get(nodeId);
  if (!center) {
    return { centerId: nodeId, nodes: [], links: [], depth };
  }

  const visited = new Set<string>([nodeId]);
  const collectedLinks: CitationLink[] = [];
  let frontier = new Set<string>([nodeId]);

  for (let d = 0; d < depth; d++) {
    const nextFrontier = new Set<string>();
    for (const link of graph.links) {
      const touches = frontier.has(link.from) || frontier.has(link.to);
      if (!touches) continue;
      collectedLinks.push(link);
      for (const id of [link.from, link.to]) {
        if (!visited.has(id)) {
          visited.add(id);
          nextFrontier.add(id);
        }
      }
    }
    frontier = nextFrontier;
  }

  const nodes = [...visited]
    .map((id) => nodeMap.get(id))
    .filter((n): n is CitationNode => Boolean(n));

  return {
    centerId: nodeId,
    nodes,
    links: collectedLinks,
    depth,
  };
}
