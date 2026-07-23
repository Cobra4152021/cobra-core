import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  buildOrgTree,
  flattenOrgUnits,
  validateNesting,
  buildAuthorizeUrlStub,
  normalizeSsoConfig,
  mapMembershipToScimUser,
  applyRoleMapping,
  PolicyEngine,
  transitionApproval,
  buildApprovalChain,
  evaluateModelAllowlist,
  routeModel,
  normalizeByomEndpoint,
  seatCheck,
  packLicense,
  filterAuditEvents,
  categorizeAuditAction,
  buildAuditFacets,
  ENTERPRISE_DOMAIN,
  DEPLOYMENT_PROFILES,
} from "../src/enterprise/index.js";

describe("KC-010 Enterprise Platform", () => {
  it("builds org tree and validates nesting", () => {
    const units = [
      { id: "bu1", name: "Operations", kind: "business_unit" as const },
      { id: "dept1", name: "Audit", kind: "department" as const, parentId: "bu1" },
      {
        id: "team1",
        name: "Field Team",
        kind: "team" as const,
        parentId: "dept1",
        memberUserIds: ["u1", "u2"],
      },
    ];

    const tree = buildOrgTree(units);
    assert.equal(tree.length, 1);
    assert.equal(tree[0].unit.id, "bu1");
    assert.equal(tree[0].children[0].unit.id, "dept1");
    assert.equal(tree[0].children[0].children[0].unit.id, "team1");

    const flat = flattenOrgUnits(units);
    assert.deepEqual(
      flat.map((u) => u.id),
      ["bu1", "dept1", "team1"],
    );

    assert.equal(validateNesting(units).length, 0);

    const cyclic = [
      { id: "a", name: "A", kind: "department" as const, parentId: "b" },
      { id: "b", name: "B", kind: "department" as const, parentId: "a" },
    ];
    const issues = validateNesting(cyclic);
    assert.ok(issues.some((i) => i.code === "cycle"));
  });

  it("builds deterministic SSO authorize stub", () => {
    const config = normalizeSsoConfig({
      provider: "okta",
      issuer: "https://example.okta.com/",
      clientId: "client-abc",
      redirectUri: "https://app.example.com/callback",
    });

    const url = buildAuthorizeUrlStub(config, "state-123");
    assert.ok(url.startsWith("https://example.okta.com/authorize?"));
    assert.ok(url.includes("client_id=client-abc"));
    assert.ok(url.includes("redirect_uri="));
    assert.ok(url.includes("state=state-123"));
    assert.ok(url.includes("provider=okta"));

    const url2 = buildAuthorizeUrlStub(config, "state-123");
    assert.equal(url, url2);
  });

  it("maps SCIM user and applies role mapping", () => {
    const payload = {
      userName: "jane.doe@example.com",
      name: { givenName: "Jane", familyName: "Doe" },
      emails: [{ value: "jane.doe@example.com", primary: true }],
      groups: ["corp-analysts"],
    };

    const user = mapMembershipToScimUser(payload, { id: "scim-1" });
    assert.equal(user.id, "scim-1");
    assert.equal(user.displayName, "Jane Doe");
    assert.equal(user.active, true);

    const mapped = applyRoleMapping(user, ["corp-analysts"], [
      { groupPattern: "corp-*", role: "analyst" },
    ]);
    assert.ok(mapped.roles.includes("analyst"));
  });

  it("denies cross-resource policy access for viewer", () => {
    const engine = new PolicyEngine([
      {
        id: "p1",
        orgId: "org1",
        name: "deny marketplace publish",
        enabled: true,
        rules: [
          {
            id: "r1",
            action: "publish",
            resourceType: "marketplace",
            roles: ["*"],
            effect: "deny",
          },
        ],
      },
    ]);

    const sdkDenied = engine.evaluatePolicy({
      actorRole: "viewer",
      action: "install",
      resourceType: "sdk",
      resourceId: "pkg-1",
      orgId: "org1",
    });
    assert.equal(sdkDenied.decision, "deny");

    const reportAllowed = engine.evaluatePolicy({
      actorRole: "viewer",
      action: "read",
      resourceType: "report",
      resourceId: "rpt-1",
      orgId: "org1",
    });
    assert.equal(reportAllowed.decision, "allow");

    const marketplacePublish = engine.evaluatePolicy({
      actorRole: "admin",
      action: "publish",
      resourceType: "marketplace",
      resourceId: "listing-1",
      orgId: "org1",
    });
    assert.equal(marketplacePublish.decision, "deny");
  });

  it("runs approval FSM transitions", () => {
    let state = "draft" as const;
    const submit = transitionApproval(state, "submit_for_review");
    assert.equal(submit.ok, true);
    state = submit.nextState!;
    assert.equal(state, "review");

    const approve = transitionApproval(state, "approve");
    assert.equal(approve.ok, true);
    state = approve.nextState!;
    assert.equal(state, "approved");

    const publish = transitionApproval(state, "publish");
    assert.equal(publish.ok, true);
    assert.equal(publish.nextState, "published");

    const invalid = transitionApproval("draft", "publish");
    assert.equal(invalid.ok, false);

    const chain = buildApprovalChain({ requireLegal: true });
    assert.ok(chain.some((s) => s.role === "legal"));
    assert.equal(chain[0].order, 1);
  });

  it("blocks model via AI governance allowlist", () => {
    const policy = {
      orgId: "org1",
      allowedModels: ["gpt-safe", "claude-safe"],
      blockedModels: ["gpt-unsafe"],
      maxTokensPerRequest: 8192,
      maxCostUsdPerDay: 100,
      retentionDays: 90,
      requireHumanReview: true,
    };

    const blocked = evaluateModelAllowlist(policy, "gpt-unsafe");
    assert.equal(blocked.allowed, false);

    const unknown = evaluateModelAllowlist(policy, "unknown-model");
    assert.equal(unknown.allowed, false);

    const allowed = evaluateModelAllowlist(policy, "gpt-safe");
    assert.equal(allowed.allowed, true);
  });

  it("routes BYOM model through endpoint", () => {
    const policy = {
      orgId: "org1",
      allowedModels: ["custom-model"],
      blockedModels: [],
      maxTokensPerRequest: 4096,
      maxCostUsdPerDay: 50,
      retentionDays: 30,
      requireHumanReview: false,
    };

    const endpoint = normalizeByomEndpoint({
      provider: "openai_compatible",
      baseUrl: "https://llm.internal.example.com/v1",
      modelAlias: { "custom-model": "deployed-v2" },
    });

    const routed = routeModel(policy, endpoint, { model: "custom-model", orgId: "org1" });
    assert.equal(routed.routed, true);
    assert.equal(routed.model, "deployed-v2");
    assert.ok(routed.endpoint?.includes("chat/completions"));

    const blocked = routeModel(policy, endpoint, { model: "other", orgId: "org1" });
    assert.equal(blocked.routed, false);
  });

  it("enforces licensing seat limits", () => {
    const entitlement = {
      orgId: "org1",
      edition: "enterprise",
      seatLimit: 10,
      seatsUsed: 9,
      packs: ["cobra.government", "cobra.labor"],
    };

    const oneSeat = seatCheck(entitlement, 1);
    assert.equal(oneSeat.allowed, true);

    const over = seatCheck(entitlement, 2);
    assert.equal(over.allowed, false);
    assert.ok(/Seat limit exceeded/.test(over.reason));

    const pack = packLicense(entitlement, "cobra.government");
    assert.equal(pack.allowed, true);

    const missing = packLicense(entitlement, "cobra.research");
    assert.equal(missing.allowed, false);
  });

  it("filters audit events with facets", () => {
    const events = [
      {
        id: "e1",
        orgId: "org1",
        actorUserId: "u1",
        action: "login",
        resourceType: "session",
        resourceId: "s1",
        timestamp: "2026-01-01T00:00:00Z",
      },
      {
        id: "e2",
        orgId: "org1",
        actorUserId: "u2",
        action: "permission_denied",
        resourceType: "report",
        resourceId: "r1",
        timestamp: "2026-01-02T00:00:00Z",
      },
      {
        id: "e3",
        orgId: "org2",
        actorUserId: "u3",
        action: "record_export",
        resourceType: "investigation",
        resourceId: "inv1",
        timestamp: "2026-01-03T00:00:00Z",
      },
    ];

    assert.equal(categorizeAuditAction("login"), "authentication");
    assert.equal(categorizeAuditAction("permission_denied"), "authorization");

    const filtered = filterAuditEvents(events, {
      orgId: "org1",
      category: "authorization",
    });
    assert.equal(filtered.length, 1);
    assert.equal(filtered[0].id, "e2");

    const facets = buildAuditFacets(events.filter((e) => e.orgId === "org1"));
    assert.equal(facets.categories.authentication, 1);
    assert.equal(facets.categories.authorization, 1);
  });

  it("exposes enterprise domain metadata and deployment profiles", () => {
    assert.equal(ENTERPRISE_DOMAIN.id, "enterprise");
    assert.ok(ENTERPRISE_DOMAIN.defaultDisclaimers.length >= 5);
    assert.equal(DEPLOYMENT_PROFILES.cloud.id, "cloud");
    assert.equal(DEPLOYMENT_PROFILES.air_gapped.requiresInternet, false);
    assert.equal(DEPLOYMENT_PROFILES.single_node.maxNodes, 1);
  });
});
