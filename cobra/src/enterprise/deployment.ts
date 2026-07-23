import type { DeploymentProfile, DeploymentProfileId } from "./types.js";

export const DEPLOYMENT_PROFILES: Record<DeploymentProfileId, DeploymentProfile> = {
  cloud: {
    id: "cloud",
    name: "Cloud SaaS",
    description: "Fully managed multi-tenant cloud deployment with vendor-operated infrastructure.",
    requiresInternet: true,
    supportsByom: true,
    supportsSso: true,
    maxNodes: null,
  },
  hybrid: {
    id: "hybrid",
    name: "Hybrid",
    description: "Control plane in cloud with customer-managed data plane or VPC peering.",
    requiresInternet: true,
    supportsByom: true,
    supportsSso: true,
    maxNodes: null,
  },
  air_gapped: {
    id: "air_gapped",
    name: "Air-Gapped",
    description: "No outbound internet; updates and models delivered via secure transfer.",
    requiresInternet: false,
    supportsByom: true,
    supportsSso: true,
    maxNodes: null,
  },
  on_premises: {
    id: "on_premises",
    name: "On-Premises",
    description: "Customer-operated datacenter deployment with optional vendor support.",
    requiresInternet: false,
    supportsByom: true,
    supportsSso: true,
    maxNodes: null,
  },
  single_node: {
    id: "single_node",
    name: "Single Node",
    description: "All services on one node for pilots and edge deployments.",
    requiresInternet: false,
    supportsByom: false,
    supportsSso: false,
    maxNodes: 1,
  },
  ha: {
    id: "ha",
    name: "High Availability",
    description: "Multi-node active/active or active/passive cluster with shared state.",
    requiresInternet: false,
    supportsByom: true,
    supportsSso: true,
    maxNodes: null,
  },
};

/** Lookup deployment profile by id. */
export function getDeploymentProfile(id: DeploymentProfileId): DeploymentProfile {
  return DEPLOYMENT_PROFILES[id];
}

/** List all deployment profiles. */
export function listDeploymentProfiles(): DeploymentProfile[] {
  return Object.values(DEPLOYMENT_PROFILES);
}

/** Check if profile supports a capability. */
export function profileSupports(
  id: DeploymentProfileId,
  capability: "byom" | "sso" | "internet",
): boolean {
  const profile = DEPLOYMENT_PROFILES[id];
  switch (capability) {
    case "byom":
      return profile.supportsByom;
    case "sso":
      return profile.supportsSso;
    case "internet":
      return profile.requiresInternet;
    default:
      return false;
  }
}
