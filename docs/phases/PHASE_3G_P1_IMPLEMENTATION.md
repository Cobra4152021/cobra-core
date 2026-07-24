# Phase 3G Priority 1 — Implementation record

**Baseline:** `phase-3f-qualified` / `0a2af49ee86451c374a600579d3644c811cd12c0`  
**State:** Implemented (tooling + documentation)  
**Runtime requalification required:** **No**

## Task ledger

| ID | Task | Changed files | Expected operational benefit | Technical risk | Requal? |
| --- | --- | --- | --- | --- | --- |
| P1-01 | SSH bootstrap + setup automation | `scripts/phase3g_ssh_bootstrap.py`, `creation-commands.md` | Faster SSH recovery; fewer blocked sessions | Low | No |
| P1-02 | Pin deps + image digests | `torch-pin.json`, `container-image-pin.json`, runtime lock, `dependency-lock.sha256` | Reproducible host+venv identity | Low | No |
| P1-03 | Split runtime/dev deps | `requirements-cloud-runtime.txt`, `requirements-cloud-dev.txt`, lock alias | Smaller prod footprint | Low | No |
| P1-04 | Reproducible env creation | `creation-commands.md`, `phase3g_verify_env.py`, `environment-manifest.json` | Deterministic bring-up | Low | No |
| P1-05 | Provisioning preflight | `scripts/phase3g_provision_preflight.py` | Prevents multi-instance / bad launches | Low | No |
| P1-06 | Cleanup verification | `scripts/phase3g_cleanup_verify.py` | Reliable terminate + audit | Low–Med (explicit `--terminate`) | No |
| P1-07 | Documentation | ADR-0015, status/roadmap cross-links, env README | Clear ops + governance | None | No |
| P1-08 | Evidence generation | `phase3g_write_p1_evidence.py`, `evaluations/diagnostics/phase-3g-p1/` | Auditable P1 package | None | No |
| P1-09 | VRAM envelope | `VRAM_ENVELOPE.md` | Safe SKU sizing from measured ~6 GiB | None | No |
| P1-10 | Cost GPU recommendations | `GPU_COST_RECOMMENDATIONS.md` | Lower $/hr guidance (L4/A5000) | Low | No* |

\*New SKU adoption later needs abbreviated smoke; P1 itself only documents recommendations.

## Integrity

* CobraBench v0.2-rc2: `prepared-not-run`
* Official score: **0.840**
* No model/prompt/inference changes

## Estimated cloud savings

* **Ops-only:** ~$0.22/session (≈30 min less avoidable GPU time @ $0.44/hr)
* **SKU right-size (future, after smoke):** ~$0.19/hr indicative (A40 $0.44 → A5000 ~$0.25)
