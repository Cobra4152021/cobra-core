import type { OrgUnit } from "./types.js";

export interface OrgTreeNode {
  unit: OrgUnit;
  children: OrgTreeNode[];
}

export interface OrgValidationIssue {
  unitId: string;
  code: "duplicate_id" | "missing_parent" | "cycle" | "orphan_root";
  message: string;
}

/** Build a nested org tree from flat units (roots have no parentId). */
export function buildOrgTree(units: OrgUnit[]): OrgTreeNode[] {
  const byId = new Map(units.map((u) => [u.id, u]));
  const childrenOf = new Map<string, OrgUnit[]>();

  for (const unit of units) {
    const parentKey = unit.parentId ?? "__root__";
    const list = childrenOf.get(parentKey) ?? [];
    list.push(unit);
    childrenOf.set(parentKey, list);
  }

  const buildNode = (unit: OrgUnit): OrgTreeNode => ({
    unit,
    children: (childrenOf.get(unit.id) ?? []).map(buildNode),
  });

  const roots = childrenOf.get("__root__") ?? [];
  return roots.filter((r) => !r.parentId || !byId.has(r.parentId)).map(buildNode);
}

/** Flatten org tree depth-first. */
export function flattenOrgUnits(units: OrgUnit[]): OrgUnit[] {
  const tree = buildOrgTree(units);
  const out: OrgUnit[] = [];

  const walk = (nodes: OrgTreeNode[]): void => {
    for (const node of nodes) {
      out.push(node.unit);
      walk(node.children);
    }
  };

  walk(tree);
  return out;
}

/** Validate org nesting: unique ids, valid parents, no cycles. */
export function validateNesting(units: OrgUnit[]): OrgValidationIssue[] {
  const issues: OrgValidationIssue[] = [];
  const ids = new Set<string>();
  const byId = new Map(units.map((u) => [u.id, u]));

  for (const unit of units) {
    if (ids.has(unit.id)) {
      issues.push({
        unitId: unit.id,
        code: "duplicate_id",
        message: `Duplicate org unit id: ${unit.id}`,
      });
    }
    ids.add(unit.id);
  }

  for (const unit of units) {
    if (unit.parentId && !byId.has(unit.parentId)) {
      issues.push({
        unitId: unit.id,
        code: "missing_parent",
        message: `Parent ${unit.parentId} not found for unit ${unit.id}`,
      });
    }
  }

  const visiting = new Set<string>();
  const visited = new Set<string>();

  const detectCycle = (id: string): boolean => {
    if (visited.has(id)) return false;
    if (visiting.has(id)) return true;
    visiting.add(id);
    const unit = byId.get(id);
    if (unit?.parentId && byId.has(unit.parentId)) {
      if (detectCycle(unit.parentId)) return true;
    }
    visiting.delete(id);
    visited.add(id);
    return false;
  };

  for (const unit of units) {
    if (detectCycle(unit.id)) {
      issues.push({
        unitId: unit.id,
        code: "cycle",
        message: `Cycle detected involving unit ${unit.id}`,
      });
    }
  }

  const roots = units.filter((u) => !u.parentId);
  if (units.length > 0 && roots.length === 0) {
    issues.push({
      unitId: units[0].id,
      code: "orphan_root",
      message: "No root org unit found (all units have parents)",
    });
  }

  return issues;
}
