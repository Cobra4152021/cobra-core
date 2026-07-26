# Citation Policy

## Rule

No unsupported conclusions. Every successful Investigation Skill result includes a `citations` list.

## Format

Ranked evidence receives stable labels:

```
EV-001
EV-002
EV-003
```

## Attachment

`attach_citations_to_output` adds:

- Top-level `citations: ["EV-001", …]`
- Optional per-finding citation lists when findings are objects

## Examples

**VehicleDamageAssessment** — requires vehicle photos → citations reference those images.

**PolicyComplianceReview** — requires policy → citations reference policy items.

**BudgetAnalysis** — requires budget → citations reference budget items.

## Audit

Citation labels are recorded in KEF audit (`citations_produced`). Document bodies are never audited.
