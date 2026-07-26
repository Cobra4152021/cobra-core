# ADR-0008 — Investigation Evaluation & Benchmark Framework

## Status

Accepted (KC-030)

## Context

Cobra Investigation Skills (ISF → KEF → AIR → RRF → CIAL → Provider) need a deterministic way to measure quality without changing routing or polluting production approval queues. Existing `cobrabench` assets evaluate model lab cases; this framework evaluates **Investigation Skill** outputs against versioned gold datasets.

## Decision

Add package `cobra_core.benchmark` as a measurement-only “truth engine”:

```
Computer → Workflow → ISF → KEF → AIR → RRF → CIAL → Provider → Result
                                                              ↓
                                                      Benchmark Engine
```

The engine:

- Loads versioned datasets (expected evidence, findings, citations, confidence, schema)
- Scores accuracy, citations, schema, completeness, confidence calibration, latency, cost
- Supports repeatability and provider *comparison labels*
- Emits JSON / Markdown / HTML reports
- Records isolated audit + metrics (`benchmark_*`)

It does **not**:

- Change AIR routing or provider selection
- Self-learn or fine-tune models
- Write production investigation history or approval queues

## Consequences

- Built-in datasets cover vehicle damage, policy, contract, budget, timeline, evidence summary, document comparison
- Executors are injected (default deterministic mock for offline regression)
- Production remains disabled; framework ships for local/staging evaluation only
