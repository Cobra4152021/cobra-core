import type { SsoConfig, SsoProviderType } from "./types.js";

export interface SsoValidationIssue {
  field: string;
  message: string;
}

const VALID_PROVIDERS: readonly SsoProviderType[] = [
  "oidc",
  "saml",
  "azure_ad",
  "google_workspace",
  "okta",
  "auth0",
  "keycloak",
];

/** Normalize SSO config with defaults and trimmed strings. */
export function normalizeSsoConfig(raw: Partial<SsoConfig> & Pick<SsoConfig, "provider">): SsoConfig {
  const provider = raw.provider;
  const defaultScopes =
    provider === "saml"
      ? []
      : provider === "google_workspace"
        ? ["openid", "email", "profile"]
        : ["openid", "profile", "email"];

  return {
    provider,
    issuer: (raw.issuer ?? "").trim(),
    clientId: (raw.clientId ?? "").trim(),
    redirectUri: (raw.redirectUri ?? "").trim(),
    scopes: raw.scopes?.length ? [...raw.scopes] : defaultScopes,
    metadataUrl: raw.metadataUrl?.trim() || undefined,
  };
}

/**
 * Build a deterministic authorize URL stub from config (no network).
 * Useful for tests and integration wiring previews.
 */
export function buildAuthorizeUrlStub(config: SsoConfig, state = "cobra-sso-state"): string {
  const normalized = normalizeSsoConfig(config);
  const base = normalized.issuer.replace(/\/$/, "");
  const path =
    normalized.provider === "saml"
      ? "/saml/sso"
      : normalized.provider === "azure_ad"
        ? "/oauth2/v2.0/authorize"
        : "/authorize";

  const params = new URLSearchParams();
  params.set("client_id", normalized.clientId);
  params.set("redirect_uri", normalized.redirectUri);
  params.set("response_type", normalized.provider === "saml" ? "SAMLResponse" : "code");
  params.set("state", state);
  if (normalized.scopes?.length && normalized.provider !== "saml") {
    params.set("scope", normalized.scopes.join(" "));
  }
  params.set("provider", normalized.provider);

  return `${base}${path}?${params.toString()}`;
}

/** Validate SSO provider configuration. */
export function validateSsoProvider(config: SsoConfig): SsoValidationIssue[] {
  const issues: SsoValidationIssue[] = [];
  const normalized = normalizeSsoConfig(config);

  if (!VALID_PROVIDERS.includes(normalized.provider)) {
    issues.push({ field: "provider", message: `Unsupported provider: ${normalized.provider}` });
  }

  if (!normalized.issuer) {
    issues.push({ field: "issuer", message: "Issuer is required" });
  } else if (!/^https?:\/\//i.test(normalized.issuer)) {
    issues.push({ field: "issuer", message: "Issuer must be an http(s) URL" });
  }

  if (!normalized.clientId) {
    issues.push({ field: "clientId", message: "Client ID is required" });
  }

  if (!normalized.redirectUri) {
    issues.push({ field: "redirectUri", message: "Redirect URI is required" });
  } else if (!/^https?:\/\//i.test(normalized.redirectUri)) {
    issues.push({ field: "redirectUri", message: "Redirect URI must be an http(s) URL" });
  }

  if (normalized.provider === "saml" && !normalized.metadataUrl) {
    issues.push({ field: "metadataUrl", message: "SAML provider requires metadataUrl" });
  }

  return issues;
}
