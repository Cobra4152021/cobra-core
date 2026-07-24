# Product positioning — Cobra Core

## 1. Category

**Evidence-first analytical model** (investigation & research grade), delivered with a disciplined model lab — not a general consumer assistant and not a case-management application.

## 2. Positioning statement

For **investigators, researchers, and high-scrutiny analysts** who must ground conclusions in sources, **Cobra Core** is the evidence-first model line that prioritizes citation discipline, contradiction detection, and calibrated uncertainty. Unlike general chat models optimized for fluency, Cobra is evaluated for **refusal to invent** and for structured analytical outputs. Unlike **Cobra Investigator**, Core is the model + lab — not the product UI, vault, or workflow system.

## 3. Positioning vs alternatives

| Alternative | They optimize for | Cobra differentiates by |
| --- | --- | --- |
| General LLMs (ChatGPT-class) | Breadth, fluency, tools | Grounding, contradiction, confidence; lab integrity |
| Code-specialist models | Repo agents, codegen | Code is supporting pillar (P5), not the mission |
| RAG “answer engines” | Retrieval UX | Model behavior under supplied evidence packs; explicit unknowns |
| Benchmark-chasing releases | Leaderboard deltas | Versioned official scores; separate workload validation |
| Cobra Investigator | End-user investigation product | Clear boundary: app vs model lab |

## 4. Messaging pillars (external-facing, when authorized)

1. **Show your work** — every material claim needs a source or an “unknown.”  
2. **Conflicts are first-class** — disagreement is reported, not averaged away.  
3. **Confidence you can audit** — strength of belief is part of the answer.  
4. **Built under evaluation discipline** — qualified runtimes and immutable official scores.

## 5. Anti-messaging (do not claim)

- “Court-ready autonomous conclusions”  
- “Replaces detectives / attorneys / analysts”  
- “Beats 0.840” without a new official protocol/run  
- “Production deployed” without deploy authorization  
- “Trained on your private cases” (not a Core promise)

## 6. Package architecture (how the story fits the repo)

```text
Cobra Investigator (separate product)
        ↑ consumes
Cobra Core model line (designated later)
        ↑ validated by
Phase 4 capability suite + CobraBench (versioned)
        ↑ runs on
Qualified runtime (phase-3f-qualified today)
        ↑ governed in
Cobra Model Lab (this repository)
```

## 7. Go-to-market posture (future)

| Stage | Posture |
| --- | --- |
| Alpha (now) | Internal / partner-technical only; no capability-pass claims |
| Beta | Share workload validation summaries with caveats |
| RC | Reproducible packs for design partners |
| 1.0 | Designated model line; Investigator integration optional |

## 8. Success of positioning

Positioning succeeds when buyers and builders can answer in one sentence:

> “Cobra Core is the evidence-first model; Investigator is the app; the lab keeps them honest.”
