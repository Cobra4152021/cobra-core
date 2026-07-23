# KC-009 — Cobra Research Edition Final Report

**Status:** Pending verification  
**Branch:** `kc-009-research-core`  
**Pack ID:** `cobra.research`  
**Version:** 0.1.0

## Summary

KC-009 delivers the Cobra Research Edition domain pack as a self-contained module under `cobra/src/investigator/domains/research/`, registered through the KC-008 domain SDK `PACK_BUILDERS` mechanism.

## Deliverables

| Item | Status |
|------|--------|
| Domain module (12 files) | Built |
| SDK wiring (builtin, registry, sandbox) | Built |
| Investigator export (`research` namespace) | Built |
| Tests (`research.test.ts`) | Built |
| Architecture doc | Complete |
| npm test | Green (73/73) |
| npm run typecheck | Green |

## Scope

### Included

- 9 research templates including anomaly investigation
- Source reliability heuristics (deterministic, disclaimer-backed)
- Evidence matrix with relation types
- Competing hypotheses workspace
- Research timeline with kind filtering
- Citation graph explorer
- Report sections with mandatory disclaimers
- 6 research metrics
- Marketplace registration as `Research` category

### Not Included

- UI widgets (viz contributions registered; rendering deferred)
- LLM integration for synthesis
- Production deployment
- Hidden Grid OS runtime coupling (domain-neutral design)

## Verification Checklist

- [x] `npm test` green
- [x] `npm run typecheck` green
- [x] Registry lists `cobra.research` with 9 templates
- [x] Marketplace catalog shows research as installable
- [x] Sandbox accepts `research.*` permissions

## Risks

- Reliability scores are heuristic only; misuse without human review is a product risk
- Anomaly template is intentionally domain-neutral; downstream apps must add jurisdiction-specific disclaimers

## Next Steps

1. Run full test suite and typecheck
2. Integrate research template routing in strategy engine (optional)
3. Wire viz widgets in Intelligence Studio when UI milestone begins
