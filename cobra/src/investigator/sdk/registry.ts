/** KC-008 — in-memory domain pack registry. */

import {
  createAllBuiltInPacks,
  createBuiltInGovernmentPack,
  createBuiltInLaborPack,
  createBuiltInStudioPack,
} from "./builtin.js";
import type {
  DomainPackRegistration,
  MetricRegistration,
  ReportLayoutRegistration,
  TemplateRegistration,
  VisualizationContribution,
} from "./types.js";

export class DomainPackRegistry {
  private readonly packs = new Map<string, DomainPackRegistration>();

  registerPack(registration: DomainPackRegistration): void {
    if (this.packs.has(registration.packId)) {
      throw new Error(`Pack already registered: ${registration.packId}`);
    }
    this.packs.set(registration.packId, { ...registration });
  }

  getPack(id: string): DomainPackRegistration | undefined {
    const pack = this.packs.get(id);
    return pack ? { ...pack } : undefined;
  }

  listPacks(): DomainPackRegistration[] {
    return [...this.packs.values()].map((p) => ({ ...p }));
  }

  listTemplates(): TemplateRegistration[] {
    return this.listPacks().flatMap((p) => p.templates.map((t) => ({ ...t })));
  }

  listMetrics(): MetricRegistration[] {
    return this.listPacks().flatMap((p) => p.metrics.map((m) => ({ ...m })));
  }

  listReportLayouts(): ReportLayoutRegistration[] {
    return this.listPacks().flatMap((p) => p.reportLayouts.map((r) => ({ ...r })));
  }

  listVisualizations(): VisualizationContribution[] {
    return this.listPacks().flatMap((p) => p.visualizations.map((v) => ({ ...v })));
  }
}

/** Registry pre-loaded with built-in government, labor, and studio packs. */
export function createDefaultRegistry(): DomainPackRegistry {
  const registry = new DomainPackRegistry();
  for (const pack of createAllBuiltInPacks()) {
    registry.registerPack(pack);
  }
  return registry;
}

/** Registry with government + labor built-ins only (common alpha1 default). */
export function createCoreRegistry(): DomainPackRegistry {
  const registry = new DomainPackRegistry();
  registry.registerPack(createBuiltInGovernmentPack());
  registry.registerPack(createBuiltInLaborPack());
  return registry;
}

export {
  createBuiltInGovernmentPack,
  createBuiltInLaborPack,
  createBuiltInStudioPack,
  createAllBuiltInPacks,
};
