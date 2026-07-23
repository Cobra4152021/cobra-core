/** Cobra Research domain pack registration (KC-009). */

import type { DomainPackRegistry } from "../../sdk/registry.js";
import type { DomainPackRegistration, PluginManifest } from "../../sdk/types.js";
import { RESEARCH_DEFAULT_REPORT_SECTIONS } from "./report.js";
import { listResearchTemplates } from "./templates.js";

const RESEARCH_METRIC_IDS = [
  "evidence_density",
  "citation_coverage",
  "hypothesis_confidence",
  "research_completeness",
  "source_diversity",
  "evidence_conflicts",
] as const;

const RESEARCH_VIZ_WIDGETS = [
  { id: "research.evidenceMatrix", title: "Evidence Matrix", widgetType: "matrix" },
  { id: "research.hypotheses", title: "Hypothesis Workspace", widgetType: "hypotheses" },
  { id: "research.timeline", title: "Research Timeline", widgetType: "timeline" },
  { id: "research.citations", title: "Citation Explorer", widgetType: "graph" },
  { id: "research.reliability", title: "Source Reliability", widgetType: "reliability" },
  { id: "research.metrics", title: "Research Metrics", widgetType: "metrics" },
] as const;

function researchManifest(): PluginManifest {
  return {
    id: "cobra.research",
    name: "Cobra Research",
    version: "0.1.0",
    author: "Cobra Core",
    license: "Proprietary",
    minimumCobraVersion: "0.4.0",
    supportedEditions: ["investigator", "research", "enterprise"],
    dependencies: [],
    permissions: [
      "marketplace.view",
      "research.templates.read",
      "research.metrics.compute",
      "research.report.generate",
      "research.citations.explore",
      "use_investigator.plan",
      "use_investigator.report",
    ],
    featureFlags: [
      "RESEARCH_EVIDENCE_MATRIX",
      "RESEARCH_HYPOTHESIS_WORKSPACE",
      "RESEARCH_CITATION_EXPLORER",
      "RESEARCH_RELIABILITY_ENGINE",
    ],
    migrationList: [],
    description:
      "Evidence synthesis and research investigation workspace for literature review, field studies, intelligence assessment, and long-form anomaly investigations.",
  };
}

export function createResearchPackRegistration(): DomainPackRegistration {
  const manifest = researchManifest();
  const templates = listResearchTemplates().map((t) => ({
    id: t.id,
    title: t.title,
    packId: manifest.id,
  }));

  return {
    packId: manifest.id,
    manifest,
    category: "Research",
    signingStatus: "builtin",
    templates,
    reportLayouts: [
      {
        id: "research.default",
        title: "Research Investigation Report",
        packId: manifest.id,
        sectionIds: [...RESEARCH_DEFAULT_REPORT_SECTIONS],
      },
    ],
    metrics: RESEARCH_METRIC_IDS.map((id) => ({
      id,
      name: id.replace(/_/g, " "),
      packId: manifest.id,
      category: "research",
    })),
    visualizations: RESEARCH_VIZ_WIDGETS.map((w) => ({
      id: w.id,
      title: w.title,
      packId: manifest.id,
      widgetType: w.widgetType,
    })),
    docsPointers: ["docs/KC009_ARCHITECTURE.md", "docs/KC009_FINAL_REPORT.md"],
    enabled: true,
  };
}

export function registerResearchPack(registry: DomainPackRegistry): void {
  registry.registerPack(createResearchPackRegistration());
}
