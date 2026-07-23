# Cobra Evidence Prompt Standard (Prospective)

**Status:** Prospective diagnostic / future-benchmark convention  
**Does not modify** frozen CobraBench v0.1 case prompts.

## Recommended evidence structure

```text
[SOURCE S1]
Title: ...
Date: ...
Content:
...

[SOURCE S2]
Title: ...
Date: ...
Content:
...
```

Legacy `SRC-A` keys remain valid in CobraBench v0.1. Prospective templates may use `S1` / `[S1]` alongside `SRC-*`.

## Recommended answer convention (extended)

```text
Finding: ...
Evidence: [S1], [S2]
Inference: ...
Confidence: ...
Missing information: ...
```

## Distinctions (required vocabulary)

| Concept | Meaning |
| --- | --- |
| Source identifier | Stable key for a supplied evidence block (`S1`, `SRC-A`) |
| Evidence content | Text inside the source block |
| Factual finding | Claim presented as supported by evidence |
| Inference | Conclusion beyond direct evidence; must be labeled |
| Confidence | Calibrated certainty statement |
| Unresolved conflict | Competing accounts preserved without forced merge |
| Missing information | Explicit gaps |
| Recommended next step | Action proposal (not a factual claim) |

## Variants

### Minimal

- Source blocks + freeform answer with citation keys
- Suitable for short grounding tasks

### Extended

- Full Finding / Evidence / Inference / Confidence / Missing information structure
- Suitable for investigation diagnostics and future v0.2 cases

Not every task must use the extended structure.
