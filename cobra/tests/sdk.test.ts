import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  parseManifest,
  isSemverish,
  createDefaultRegistry,
  createBuiltInGovernmentPack,
  createBuiltInLaborPack,
  planInstall,
  planDisable,
  planRemove,
  resolveDependencies,
  checksumSha256Hex,
  verifyChecksum,
  buildSignedPackageMeta,
  assertSandboxSafe,
  buildMarketplaceCatalog,
  createAllBuiltInPacks,
} from "../src/investigator/sdk/index.js";

describe("KC-008 Domain SDK & Marketplace", () => {
  describe("manifest validation", () => {
    it("accepts valid cobra-domain.json shape", () => {
      const result = parseManifest({
        id: "community.example",
        name: "Example Pack",
        version: "1.0.0",
        author: "Example Author",
        license: "MIT",
        minimumCobraVersion: "0.4.0",
        supportedEditions: ["investigator"],
        dependencies: [{ packId: "cobra.government", optional: true }],
        permissions: ["marketplace.view", "government.templates.read"],
        featureFlags: ["example.flag"],
        migrationList: ["001_init"],
        description: "An example community pack",
      });
      assert.equal(result.ok, true);
      if (result.ok) {
        assert.equal(result.manifest.id, "community.example");
        assert.equal(result.manifest.version, "1.0.0");
      }
    });

    it("rejects missing required fields", () => {
      const result = parseManifest({ id: "bad", version: "1.0.0" });
      assert.equal(result.ok, false);
      if (!result.ok) {
        assert.ok(result.errors.some((e) => /name is required/.test(e)));
        assert.ok(result.errors.some((e) => /author is required/.test(e)));
      }
    });

    it("rejects non-semver version strings", () => {
      assert.equal(isSemverish("1.0.0"), true);
      assert.equal(isSemverish("0.4.1"), true);
      assert.equal(isSemverish("not-a-version"), false);

      const result = parseManifest({
        id: "bad.version",
        name: "Bad",
        version: "v1",
        author: "A",
        license: "MIT",
        minimumCobraVersion: "0.4.0",
        supportedEditions: ["investigator"],
        dependencies: [],
        permissions: [],
        featureFlags: [],
        migrationList: [],
      });
      assert.equal(result.ok, false);
      if (!result.ok) {
        assert.ok(result.errors.some((e) => /version must be semver/.test(e)));
      }
    });
  });

  describe("builtin packs and registry", () => {
    it("registers government, labor, and research built-in packs with templates from domains", () => {
      const registry = createDefaultRegistry();
      const packs = registry.listPacks();
      assert.ok(packs.some((p) => p.packId === "cobra.government"));
      assert.ok(packs.some((p) => p.packId === "cobra.labor"));
      assert.ok(packs.some((p) => p.packId === "cobra.research"));

      const gov = registry.getPack("cobra.government")!;
      assert.equal(gov.templates.length, 15);
      assert.ok(gov.templates.every((t) => t.id.startsWith("gov_")));
      assert.ok(gov.templates.some((t) => t.title === "Overtime Analysis"));

      const labor = registry.getPack("cobra.labor")!;
      assert.equal(labor.templates.length, 14);
      assert.ok(labor.templates.every((t) => t.id.startsWith("labor_")));

      const research = registry.getPack("cobra.research")!;
      assert.equal(research.templates.length, 9);
      assert.ok(research.templates.every((t) => t.id.startsWith("research_")));

      const allTemplates = registry.listTemplates();
      assert.equal(allTemplates.length, 15 + 14 + 9);
    });

    it("lists report layouts and metrics from built-ins", () => {
      const registry = createDefaultRegistry();
      const layouts = registry.listReportLayouts();
      assert.ok(layouts.some((l) => l.id === "government.default"));
      assert.ok(layouts.some((l) => l.id === "labor.default"));

      const metrics = registry.listMetrics();
      assert.ok(metrics.some((m) => m.id === "vacancy_rate"));
      assert.ok(metrics.some((m) => m.id === "grievance_open_count"));
    });
  });

  describe("package manager", () => {
    it("plans install for government pack", () => {
      const gov = createBuiltInGovernmentPack();
      const catalog = createAllBuiltInPacks().map((r) => ({
        packId: r.packId,
        registration: r,
      }));
      const result = planInstall(gov, [], "0.4.1", catalog);
      assert.equal(result.success, true);
      if (result.success) {
        assert.equal(result.plan.action, "install");
        assert.equal(result.plan.packId, "cobra.government");
        assert.ok(result.plan.permissionsGranted.includes("government.templates.read"));
      }
    });

    it("plans disable and remove", () => {
      const installed = [{ packId: "cobra.government", version: "0.1.0", enabled: true }];
      const disable = planDisable("cobra.government", installed);
      assert.ok(disable);
      assert.equal(disable!.action, "disable");

      const remove = planRemove("cobra.government", installed);
      assert.ok(remove);
      assert.equal(remove!.action, "remove");
    });

    it("resolves labor optional government dependency", () => {
      const catalog = createAllBuiltInPacks().map((r) => ({
        packId: r.packId,
        registration: r,
      }));
      const resolved = resolveDependencies(catalog, "cobra.labor", []);
      assert.ok(resolved.resolved.includes("cobra.labor"));
      assert.equal(resolved.missing.length, 0);
    });

    it("blocks install when cobra version too low", () => {
      const labor = createBuiltInLaborPack();
      const catalog = [{ packId: labor.packId, registration: labor }];
      const result = planInstall(labor, [], "0.1.0", catalog);
      assert.equal(result.success, false);
    });
  });

  describe("signing", () => {
    it("computes and verifies sha256 checksum", () => {
      const payload = '{"id":"cobra.government","version":"0.1.0"}';
      const hex = checksumSha256Hex(payload);
      assert.equal(hex.length, 64);
      assert.equal(verifyChecksum(payload, hex), true);
      assert.equal(verifyChecksum(payload, "deadbeef"), false);
    });

    it("builds signed package meta with builtin status", () => {
      const meta = buildSignedPackageMeta({
        packId: "cobra.government",
        publisher: "Cobra Core",
        payload: "builtin-pack",
        signingStatus: "builtin",
        versionHistory: ["0.1.0"],
      });
      assert.equal(meta.signingStatus, "builtin");
      assert.equal(meta.signature, null);
      assert.ok(meta.checksumSha256);
    });
  });

  describe("sandbox", () => {
    it("denies dangerous permissions outside allowlist", () => {
      assert.throws(
        () =>
          assertSandboxSafe({
            id: "evil.pack",
            name: "Evil",
            version: "1.0.0",
            author: "X",
            license: "MIT",
            minimumCobraVersion: "0.4.0",
            supportedEditions: ["investigator"],
            dependencies: [],
            permissions: ["filesystem.write", "network.egress"],
            featureFlags: [],
            migrationList: [],
          }),
        /Sandbox violation/,
      );
    });

    it("allows government and marketplace permissions", () => {
      const gov = createBuiltInGovernmentPack();
      assert.doesNotThrow(() => assertSandboxSafe(gov.manifest));
    });
  });

  describe("marketplace catalog", () => {
    it("includes government and labor with correct categories", () => {
      const packs = [createBuiltInGovernmentPack(), createBuiltInLaborPack()];
      const catalog = buildMarketplaceCatalog({
        packs,
        installedPackIds: ["cobra.government"],
        disabledPackIds: [],
      });

      const gov = catalog.find((e) => e.packId === "cobra.government");
      const labor = catalog.find((e) => e.packId === "cobra.labor");
      assert.ok(gov);
      assert.ok(labor);
      assert.equal(gov!.category, "Government");
      assert.equal(labor!.category, "Labor");
      assert.equal(gov!.status, "installed");
      assert.equal(labor!.status, "available");
      assert.equal(gov!.templateCount, 15);
      assert.equal(labor!.templateCount, 14);
    });
  });
});
