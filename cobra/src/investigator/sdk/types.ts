/** KC-008 Domain SDK & Marketplace — core types. */

export type PackSigningStatus = "builtin" | "unsigned" | "verified";

export type MarketplaceCategory =
  | "Government"
  | "Labor"
  | "Research"
  | "Enterprise"
  | "Community";

export type MarketplaceEntryStatus = "available" | "installed" | "disabled";

export interface PackDependency {
  packId: string;
  versionRange?: string;
  optional?: boolean;
}

export interface PackPermission {
  id: string;
  description?: string;
}

export interface PackFeatureFlag {
  key: string;
  defaultEnabled?: boolean;
  description?: string;
}

/** Shape of `cobra-domain.json` for a domain pack plugin. */
export interface PluginManifest {
  id: string;
  name: string;
  version: string;
  author: string;
  license: string;
  minimumCobraVersion: string;
  supportedEditions: string[];
  dependencies: PackDependency[];
  permissions: Array<PackPermission | string>;
  featureFlags: Array<PackFeatureFlag | string>;
  migrationList: string[];
  description?: string;
}

export interface TemplateRegistration {
  id: string;
  title: string;
  packId: string;
}

export interface ReportLayoutRegistration {
  id: string;
  title: string;
  packId: string;
  sectionIds: string[];
}

export interface MetricRegistration {
  id: string;
  name: string;
  packId: string;
  category?: string;
}

export interface VisualizationContribution {
  id: string;
  title: string;
  packId: string;
  widgetType: string;
}

export interface DomainPackRegistration {
  packId: string;
  manifest: PluginManifest;
  category: MarketplaceCategory;
  signingStatus: PackSigningStatus;
  templates: TemplateRegistration[];
  reportLayouts: ReportLayoutRegistration[];
  metrics: MetricRegistration[];
  visualizations: VisualizationContribution[];
  docsPointers: string[];
  enabled: boolean;
}

export interface CompatibilityResult {
  compatible: boolean;
  errors: string[];
  warnings: string[];
}

export type InstallPlanAction = "install" | "upgrade" | "disable" | "remove";

export interface InstallPlan {
  action: InstallPlanAction;
  packId: string;
  version: string;
  dependenciesToInstall: string[];
  permissionsGranted: string[];
  featureFlagsEnabled: string[];
  warnings: string[];
}

export interface SignedPackageMeta {
  packId: string;
  publisher: string;
  signature: string | null;
  checksumSha256: string;
  versionHistory: string[];
  signingStatus: PackSigningStatus;
}

export interface MarketplaceCatalogEntry {
  packId: string;
  name: string;
  version: string;
  author: string;
  description: string;
  category: MarketplaceCategory;
  status: MarketplaceEntryStatus;
  signingStatus: PackSigningStatus;
  templateCount: number;
  metricCount: number;
  permissions: string[];
}

export type PlanInstallResult =
  | { success: true; plan: InstallPlan }
  | { success: false; compatibility: CompatibilityResult };

export type PlanUpgradeResult =
  | { success: true; plan: InstallPlan }
  | { success: false; compatibility: CompatibilityResult };

export interface InstalledPackRef {
  packId: string;
  version: string;
  enabled: boolean;
}

export interface CatalogPackRef {
  packId: string;
  registration: DomainPackRegistration;
}
