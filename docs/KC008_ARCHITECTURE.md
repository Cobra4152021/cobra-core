# KC-008 — Domain SDK & Marketplace Architecture (cobra-core)

Pure TypeScript SDK under `cobra/src/investigator/sdk/` — sibling to `domains/`, not a domain edition.

## Purpose

Provide a manifest-driven plugin model for Cobra domain packs: registration, marketplace catalog, install planning, checksum signing scaffold, and sandbox permission enforcement.

## Module layout

| Module | Responsibility |
|--------|----------------|
| `types.ts` | Core interfaces: `PluginManifest`, `DomainPackRegistration`, `InstallPlan`, etc. |
| `manifest.ts` | Parse/validate `cobra-domain.json` (fail closed) |
| `registry.ts` | In-memory `DomainPackRegistry` |
| `builtin.ts` | Built-in adapters for `cobra.government`, `cobra.labor`, `cobra.studio` |
| `packageManager.ts` | Pure install/upgrade/disable/remove planning |
| `signing.ts` | SHA-256 checksum + signed metadata scaffold |
| `sandbox.ts` | Permission allowlist + `assertSandboxSafe` |
| `marketplace.ts` | `buildMarketplaceCatalog` |
| `index.ts` | Re-exports |

## Built-in packs

Built-ins **import** template id/title lists from existing domain modules (`listGovernmentTemplates`, `listLaborTemplates`). Template bodies are not duplicated.

- `cobra.government` — 15 templates, government report layout, 23 metrics
- `cobra.labor` — 14 templates, labor report layout, labor metrics
- `cobra.studio` — visualization widgets, studio metrics (optional third built-in)

## Manifest shape (`cobra-domain.json`)

Required: `id`, `name`, `version`, `author`, `license`, `minimumCobraVersion`, `supportedEditions`, `dependencies`, `permissions`, `featureFlags`, `migrationList`.

Optional: `description`.

Versions must be semver-ish (`x.y.z`).

## Sandbox (alpha1)

Permissions must match allowlist patterns:

- `marketplace.view`
- `government.*`, `labor.*`, `studio.*`
- `use_investigator.plan|report|metrics|templates|evidence`

## Export

```typescript
import { sdk } from "@cobra-core/knowledge-engine/investigator";
// or
import { createDefaultRegistry, buildMarketplaceCatalog } from "./investigator/sdk/index.js";
```

Investigator index: `export * as sdk from "./sdk/index.js"`.

## Verification

```bash
cd cobra && npm run typecheck && npm test
```

See `KC008_FINAL_REPORT.md` for milestone status.
