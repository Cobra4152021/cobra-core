# Recommended execution order (when authorized)

Run on the locked `phase-3f-qualified` runtime. Stop the cloud session between waves if cost-controlling.

## Wave 0 — Integrity (mandatory first)

1. Env verify (`phase3g_verify_env.py`)
2. REL-04 (malformed) — fail-safe behavior early
3. RS-05 (citation allowlist) — grounding canary
4. INV-08 (overclaim refusal) — safety canary

If Wave 0 hard-fails: **abort suite** (Suite Fail / Invalid risk).

## Wave 1 — Core mission (Investigator + Research)

5. INV-05 → INV-06 → INV-07 → INV-01 → INV-02 → INV-03 → INV-04  
6. RS-04 → RS-06 → RS-01 → RS-02 → RS-03 → RS-07 → RS-08  

## Wave 2 — Reliability stability

7. REL-01 (N=3) → REL-03 → REL-02 → REL-05 → REL-06 → REL-07  

## Wave 3 — Code (daily usefulness)

8. CG-12 → CG-01 → CG-02 → CG-06 → CG-04 → CG-13 → CG-03 → CG-07  
9. CG-14 → CG-15 → CG-08 → CG-09  
10. CG-10 → CG-11 (Workers last; more niche)

## Wave 4 — Business

11. BZ-03 → BZ-05 → BZ-01 → BZ-04 → BZ-06 → BZ-02 → BZ-07 → BZ-08  

## Wave 5 — Closeout

12. Re-spot-check one Research + one Investigator task if context cache concerns exist  
13. Score aggregation → domain gates → suite gate  
14. Export evidence + cleanup terminate  

## Parallelism

- Do **not** parallelize across multiple GPUs (authorization: one instance).  
- Human scoring may proceed offline in parallel with later waves after outputs are exported.
