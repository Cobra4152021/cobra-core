/** Studio navigation catalog (KC-007). */

export type StudioNavId =
  | "dashboard"
  | "investigations"
  | "timeline"
  | "graph"
  | "analytics"
  | "reports"
  | "search"
  | "government"
  | "labor"
  | "settings";

export interface StudioNavItem {
  id: StudioNavId;
  label: string;
  path: string;
  description: string;
}

export const STUDIO_NAV: StudioNavItem[] = [
  {
    id: "dashboard",
    label: "Dashboard",
    path: "/studio/dashboard",
    description: "Executive overview and KPIs",
  },
  {
    id: "investigations",
    label: "Investigations",
    path: "/studio/investigations",
    description: "Active and completed investigations",
  },
  {
    id: "timeline",
    label: "Timeline",
    path: "/studio/timeline",
    description: "Unified evidence and activity timeline",
  },
  {
    id: "graph",
    label: "Graph",
    path: "/studio/graph",
    description: "Relationship graph explorer",
  },
  {
    id: "analytics",
    label: "Analytics",
    path: "/studio/analytics",
    description: "Metrics, heatmaps, and trends",
  },
  {
    id: "reports",
    label: "Reports",
    path: "/studio/reports",
    description: "Report designer and exports",
  },
  {
    id: "search",
    label: "Search",
    path: "/studio/search",
    description: "Unified search across domains",
  },
  {
    id: "government",
    label: "Government",
    path: "/studio/government",
    description: "Government domain visualizations",
  },
  {
    id: "labor",
    label: "Labor",
    path: "/studio/labor",
    description: "Labor domain visualizations",
  },
  {
    id: "settings",
    label: "Settings",
    path: "/studio/settings",
    description: "Studio preferences and access",
  },
];
