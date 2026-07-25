# KC-019 — Test Plan (Phase 1)

## Unit suites

| File | Coverage |
|------|----------|
| `tests/test_cial_registry.py` | Registration, duplicates, lookup, config defaults, error translation |
| `tests/test_cial_routing.py` | Policies, eligibility, manual validation, tie-breakers, degraded |
| `tests/test_cial_mock_provider.py` | Mock generate, engine identity, InferenceService path, fail hook |

## Regression

Run full Core suite (excludes `integration` / `model_required` by default):

```bash
python -m pytest
python scripts/run_lint.py
python scripts/run_format_check.py
python scripts/run_typecheck.py
```

Protocol V1 conformance and RC1 controls must remain green (KC-018 behavior).

## Manual / staging checks (not automated in Phase 1)

1. Mock completion content still `[mock] …`
2. Wire `model` remains `cobra-core-qwen3-8b`
3. Computer proposal flow still reaches `pending_approval` (Computer-side;
   Core only preserves mock identity and Protocol V1 shape)
4. `COBRA_CORE_REVISION` pin unchanged by this work
5. No provider secrets in tree / env examples beyond placeholders

## Exit criteria

- Zero regressions on default pytest
- CIAL unit tests pass
- No Protocol V1 schema changes
- No certification tag until later review
