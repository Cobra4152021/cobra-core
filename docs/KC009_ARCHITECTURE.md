# KC-009 — Cobra Research Edition Architecture

**Status:** Alpha (v0.1.0)  
**Branch:** `kc-009-research-core`

## Overview

KC-009 adds the **Cobra Research Edition** domain pack (`cobra.research`) to cobra-core. The pack provides evidence synthesis, source reliability heuristics, hypothesis workspaces, citation exploration, and long-form anomaly investigation templates — without embedding research logic in the SDK builtin layer.

## Module Layout

```
cobra/src/investigator/domains/research/
├── domain.ts          # Domain id, version, disclaimers
├── taxonomy.ts        # Evidence categories
├── templates.ts       # 9 investigation templates
├── reliability.ts     # SourceReliabilityEngine (heuristic)
├── evidenceMatrix.ts  # Matrix builder + summarize
├── hypotheses.ts      # Competing hypotheses workspace
├── timeline.ts        # Research timeline + filter
├── citations.ts       # Citation graph explorer
├── report.ts          # Report sections + markdown render
├── metrics.ts         # Research completeness metrics
├── pack.ts            # DomainPackRegistration + registry hook
└── index.ts           # Public exports
```

## SDK Integration

Research registers through `PACK_BUILDERS` in `sdk/builtin.ts`:

- `createResearchPackRegistration()` lives in `domains/research/pack.ts`
- `createAllBuiltInPacks()` maps over `PACK_BUILDERS` (government, labor, studio, research)
- `registerResearchPack(registry)` available for explicit registration
- Sandbox allowlist extended with `research.*` permissions

## Templates (9)

| ID | Strategy | Focus |
|----|----------|-------|
| `research_literature_review` | research_investigation | Published literature survey |
| `research_evidence_synthesis` | evidence_review | Heterogeneous source matrix |
| `research_historical_investigation` | research_investigation | Archival reconstruction |
| `research_environmental_study` | research_investigation | Environmental/geographic correlation |
| `research_technical_root_cause` | technical_root_cause | Technical failure analysis |
| `research_intelligence_assessment` | evidence_review | Mixed-source assessment |
| `research_case_study` | general_investigation | Bounded case documentation |
| `research_field_investigation` | research_investigation | Field observations |
| `research_anomaly_investigation` | research_investigation | Long-form anomaly (Hidden Grid compatible) |

## Disclaimers

All research outputs carry mandatory disclaimers:

- Evidence synthesis only — not scientific peer review
- Not legal advice
- Heuristic reliability scores require human judgment
- Human review required before publication or action

## Feature Flags

- `RESEARCH_EVIDENCE_MATRIX`
- `RESEARCH_HYPOTHESIS_WORKSPACE`
- `RESEARCH_CITATION_EXPLORER`
- `RESEARCH_RELIABILITY_ENGINE`

## Permissions

- `research.templates.read`
- `research.metrics.compute`
- `research.report.generate`
- `research.citations.explore`

## Tests

`cobra/tests/research.test.ts` covers templates, reliability, matrix, hypotheses, timeline, citations, report, metrics, registry, and marketplace install.

## Related Docs

- `docs/KC009_FINAL_REPORT.md` — delivery report (pending verification)
