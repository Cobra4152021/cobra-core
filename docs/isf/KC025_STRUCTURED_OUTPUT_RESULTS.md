# KC-025 — Structured Output Parsing Results

## Behavior

Provider content is parsed by `src/cobra_core/isf/structured_json.py`:

- JSON object required (not free-form success)
- Markdown fences stripped
- Whitespace tolerated
- Truncated / non-JSON / refusal → `structured_output_invalid`
- Validated against skill Pydantic schema

## Repair

- At most **one** schema-repair attempt
- Same skill, schema, evidence refs, correlation id
- Audited via `repair_attempt_count` / `schema_validation_result`
- Failure → typed `structured_output_invalid` (never a valid proposal)

## Local unit results

| Case | Result |
|------|--------|
| JSON in fence | PASS |
| Empty / refusal | `structured_output_invalid` |
| Truncated JSON | `structured_output_invalid` |
| Repair then valid | `schema_validation_result=repaired` |
| Repair then invalid | status `structured_output_invalid` |

## Staging live (Phase 6)

All five live skills returned `pending_approval` with schema-valid `structured_result` via OpenAI (`gpt-5.4-mini`). Offline mock path uses conservative schema-shaped drafts (confidence capped).
