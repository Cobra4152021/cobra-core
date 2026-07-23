/** KC-008 — built-in domain pack registrations (thin adapters over existing domains). */

import { GOVERNMENT_DEFAULT_REPORT_SECTIONS } from "../domains/government/domain.js";
import { listGovernmentTemplates } from "../domains/government/templates.js";
import { LABOR_DEFAULT_REPORT_SECTIONS } from "../domains/labor/domain.js";
import { listLaborTemplates } from "../domains/labor/templates.js";
import { createResearchPackRegistration } from "../domains/research/pack.js";
import { STUDIO_DOMAIN } from "../domains/studio/domain.js";
import type { DomainPackRegistration, PluginManifest } from "./types.js";

/** Built-in pack registration builders — domain packs register through this list. */
export const PACK_BUILDERS: ReadonlyArray<() => DomainPackRegistration> = [
  createBuiltInGovernmentPack,
  createBuiltInLaborPack,
  createBuiltInStudioPack,
  createResearchPackRegistration,
];

const GOVERNMENT_METRIC_IDS = [
  "adopted_variance",
  "revised_variance",
  "yoy_change",
  "category_share",
  "recurring_cost_share",
  "vacancy_rate",
  "filled_rate",
  "deployable_rate",
  "attrition_rate",
  "hiring_lag",
  "overtime_hours",
  "overtime_cost",
  "average_overtime_rate",
  "overtime_per_employee",
  "overtime_per_vacancy",
  "overtime_share_of_payroll",
  "lifecycle_age",
  "maintenance_to_value_ratio",
  "downtime_rate",
  "replacement_urgency",
  "completion_rate",
  "expiration_risk",
  "missing_record_rate",
] as const;

const STUDIO_VIZ_WIDGETS = [
  { id: "studio.dashboard", title: "Executive Dashboard", widgetType: "dashboard" },
  { id: "studio.timeline", title: "Investigation Timeline", widgetType: "timeline" },
  { id: "studio.graph", title: "Relationship Graph", widgetType: "graph" },
  { id: "studio.heatmap", title: "Risk Heatmap", widgetType: "heatmap" },
  { id: "studio.metrics", title: "Metric Series", widgetType: "metrics" },
  { id: "studio.search", title: "Unified Search", widgetType: "search" },
  { id: "studio.reportDesigner", title: "Report Designer", widgetType: "report_designer" },
  { id: "studio.commandCenter", title: "Command Center", widgetType: "command_center" },
] as const;

function governmentManifest(): PluginManifest {
  return {
    id: "cobra.government",
    name: "Cobra Government",
    version: "0.1.0",
    author: "Cobra Core",
    license: "Proprietary",
    minimumCobraVersion: "0.4.0",
    supportedEditions: ["investigator", "government", "enterprise"],
    dependencies: [],
    permissions: [
      "marketplace.view",
      "government.templates.read",
      "government.metrics.compute",
      "government.report.generate",
      "use_investigator.plan",
      "use_investigator.report",
    ],
    featureFlags: ["government.pilot_scoring", "government.sensitivity_labels"],
    migrationList: [],
    description:
      "Evidence-based investigation workspace for cities, counties, public safety agencies, auditors, and labor-management review teams.",
  };
}

function laborManifest(): PluginManifest {
  return {
    id: "cobra.labor",
    name: "Cobra Labor",
    version: "0.1.0",
    author: "Cobra Core",
    license: "Proprietary",
    minimumCobraVersion: "0.4.0",
    supportedEditions: ["investigator", "labor", "enterprise"],
    dependencies: [{ packId: "cobra.government", versionRange: ">=0.1.0", optional: true }],
    permissions: [
      "marketplace.view",
      "labor.templates.read",
      "labor.report.generate",
      "labor.contracts.read",
      "use_investigator.plan",
      "use_investigator.report",
    ],
    featureFlags: ["labor.grievance_drafts", "labor.negotiation_tracking"],
    migrationList: [],
    description:
      "Evidence-based labor-management investigation workspace for CBAs, MOUs, grievances, arbitration prep, and staffing compliance.",
  };
}

function studioManifest(): PluginManifest {
  return {
    id: "cobra.studio",
    name: "Cobra Intelligence Studio",
    version: "0.1.0",
    author: "Cobra Core",
    license: "Proprietary",
    minimumCobraVersion: "0.4.0",
    supportedEditions: ["investigator", "studio", "enterprise"],
    dependencies: [
      { packId: "cobra.government", versionRange: ">=0.1.0", optional: true },
      { packId: "cobra.labor", versionRange: ">=0.1.0", optional: true },
    ],
    permissions: [
      "marketplace.view",
      "studio.dashboard.view",
      "studio.graph.view",
      "studio.metrics.view",
      "studio.report.view",
      "use_investigator.metrics",
    ],
    featureFlags: ["studio.command_center", "studio.observability"],
    migrationList: [],
    description: STUDIO_DOMAIN.description,
  };
}

export function createBuiltInGovernmentPack(): DomainPackRegistration {
  const manifest = governmentManifest();
  const templates = listGovernmentTemplates().map((t) => ({
    id: t.id,
    title: t.title,
    packId: manifest.id,
  }));

  return {
    packId: manifest.id,
    manifest,
    category: "Government",
    signingStatus: "builtin",
    templates,
    reportLayouts: [
      {
        id: "government.default",
        title: "Government Investigation Report",
        packId: manifest.id,
        sectionIds: [...GOVERNMENT_DEFAULT_REPORT_SECTIONS],
      },
    ],
    metrics: GOVERNMENT_METRIC_IDS.map((id) => ({
      id,
      name: id.replace(/_/g, " "),
      packId: manifest.id,
      category: id.includes("overtime")
        ? "overtime"
        : id.includes("vacancy") || id.includes("filled") || id.includes("staff")
          ? "staffing"
          : "budget",
    })),
    visualizations: [],
    docsPointers: ["docs/KC005_ARCHITECTURE.md"],
    enabled: true,
  };
}

export function createBuiltInLaborPack(): DomainPackRegistration {
  const manifest = laborManifest();
  const templates = listLaborTemplates().map((t) => ({
    id: t.id,
    title: t.title,
    packId: manifest.id,
  }));

  return {
    packId: manifest.id,
    manifest,
    category: "Labor",
    signingStatus: "builtin",
    templates,
    reportLayouts: [
      {
        id: "labor.default",
        title: "Labor Investigation Report",
        packId: manifest.id,
        sectionIds: [...LABOR_DEFAULT_REPORT_SECTIONS],
      },
    ],
    metrics: [
      { id: "contract_article_count", name: "Contract article count", packId: manifest.id, category: "contracts" },
      { id: "grievance_open_count", name: "Open grievances", packId: manifest.id, category: "grievance" },
      { id: "staffing_compliance_gap", name: "Staffing compliance gap", packId: manifest.id, category: "staffing" },
    ],
    visualizations: [],
    docsPointers: ["docs/KC006_ARCHITECTURE.md"],
    enabled: true,
  };
}

export function createBuiltInStudioPack(): DomainPackRegistration {
  const manifest = studioManifest();

  return {
    packId: manifest.id,
    manifest,
    category: "Enterprise",
    signingStatus: "builtin",
    templates: [],
    reportLayouts: [
      {
        id: "studio.executive",
        title: "Executive Studio Report",
        packId: manifest.id,
        sectionIds: ["dashboard", "timeline", "metrics", "findings", "citations"],
      },
    ],
    metrics: [
      { id: "budget_trends", name: "Budget trends", packId: manifest.id, category: "government" },
      { id: "overtime", name: "Overtime", packId: manifest.id, category: "shared" },
      { id: "vacancies", name: "Vacancies", packId: manifest.id, category: "government" },
      { id: "staffing", name: "Staffing", packId: manifest.id, category: "shared" },
      { id: "pilot_success", name: "Pilot success", packId: manifest.id, category: "shared" },
      { id: "investigation_duration", name: "Investigation duration", packId: manifest.id, category: "shared" },
      { id: "evidence_quality", name: "Evidence quality", packId: manifest.id, category: "shared" },
      { id: "missing_evidence", name: "Missing evidence", packId: manifest.id, category: "shared" },
      { id: "confidence", name: "Confidence", packId: manifest.id, category: "shared" },
    ],
    visualizations: STUDIO_VIZ_WIDGETS.map((w) => ({
      id: w.id,
      title: w.title,
      packId: manifest.id,
      widgetType: w.widgetType,
    })),
    docsPointers: ["docs/KC007_ARCHITECTURE.md"],
    enabled: true,
  };
}

export function createAllBuiltInPacks(): DomainPackRegistration[] {
  return PACK_BUILDERS.map((builder) => builder());
}
