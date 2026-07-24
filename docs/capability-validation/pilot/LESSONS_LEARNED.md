# Phase 4.2 — Lessons learned

## Framework practicality

1. **The catalog + rubric are usable end-to-end.** Ten diverse tasks were executable and scoreable without inventing new dimensions mid-flight.
2. **Wave-0 style canaries work.** INV-08 / RS-05 / REL-04 quickly stress overclaim, citation, and malformed-input behavior.
3. **Business/docs tasks need higher token budgets** than short investigative answers (BZ-05 truncated at 512).
4. **REL-01 with fixed seed + greedy decode produced bit-identical repeats** in-session — useful, but the catalog should state whether “fresh process” is required for full suite.

## Operational / cloud

1. **Community capacity is volatile.** L4/A40 were unavailable; A5000 and 3090 were. Pilot orchestration must accept authorized fallback SKUs and record the SKU explicitly.
2. **Windows OpenSSH argv mangling** broke remote `mkdir`/`bash -lc` until base64-wrapped scripts were used.
3. **SSH port mappings change** across stop/start; every SSH/SCP must refresh `portMappings`.
4. **Torch inductor compile workers** can keep import checks alive and hang long SSH sessions — prefer short version prints and `TORCH_COMPILE_DISABLE=1` (or equivalent) during bring-up.
5. **Model download on-pod** (pinned revision) was faster/safer than scp of 15GB from the workstation for this pilot.
6. **Warm-cache load times (~3.7 s)** are not comparable to cold Phase 3F loads (~22–75 s); telemetry docs must label cold vs warm.

## Scoring / criteria gaps

1. Catalog intents are clear, but **fixture files are not yet packaged** (prompts were embedded in the worker). Full Phase 4 needs hashed fixture files.
2. No explicit criterion for **“helpful but invents a repair example”** (REL-04) — currently a soft U3 ding, not hard fail.
3. INV-05 needs a **gold contradiction set** so false-positive “contradictions” can be scored objectively.
4. BZ-03 needs a **checklist of required facts** (index-url, verify-hash command, venv name) for binary scoring.
5. Truncation should be scored as **format incompleteness**, not automatic Fail, when the partial answer already met minimum counts (BZ-05 had 5 risks).

## Product / governance

1. Pilot results must stay labeled **workload validation**, never official score.
2. SKU ≠ A40 must be called out so Beta/RC gates are not accidentally claimed.
