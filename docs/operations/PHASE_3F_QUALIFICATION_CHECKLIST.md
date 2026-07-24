# Phase 3F qualification checklist (one page)

**Goal:** Reproduce Outcome A on authorized Linux CUDA.  
**Baseline tag:** `phase-3f-qualified` (`0a2af49ee86451c374a600579d3644c811cd12c0`)  
**Do not:** run CobraBench, train, deploy, create a second pod, or change quant/prompts/model.

## Before spend

- [ ] Authorization present; ceiling known (reference: $10)
- [ ] `RUNPOD_API_KEY` set locally (not in git)
- [ ] Model inventory hash is `8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f`
- [ ] Model revision is `b968826d9c46dd6066d109eabc6255188de91218`
- [ ] Git bundle (or equivalent) ready for transfer
- [ ] `python scripts/phase3g_provision_preflight.py` reviewed OK
- [ ] SKU plan: prefer L4 / A5000 fallback / A40 adopt-only; ≥16 GB VRAM; ≥32 GB system RAM
- [ ] Image pin noted from `container-image-pin.json`

## Pod bring-up

- [ ] Exactly one on-demand GPU pod
- [ ] Volume / `/workspace` available (do not use overlay `/` for model+venv)
- [ ] `python scripts/phase3g_ssh_bootstrap.py --pod-id <ID>` succeeds
- [ ] TCP SSH works with runpodctl key

## Transfer & env

- [ ] Bundle cloned under `/workspace/cobra-core-cloud`
- [ ] Model at `/workspace/models/qwen3-8b`
- [ ] Inventory JSON on pod; hash verified
- [ ] `python3.12 -m venv .venv-qwen-cloud` activated
- [ ] `torch==2.6.0+cu124` installed from cu124 index
- [ ] `pip install -r evaluations/environments/cloud-qwen3-runtime/requirements-cloud-runtime.txt`
- [ ] `python -m pip check` clean
- [ ] `python scripts/phase3g_verify_env.py` passes

## Qualification (synthetic only)

- [ ] `export COBRA_CLOUD_MODEL_DIR=/workspace/models/qwen3-8b`
- [ ] `export COBRA_CLOUD_INVENTORY=<inventory path>`
- [ ] `python scripts/_phase3f_linux_qualify_parent.py`
- [ ] Native backend pass
- [ ] Load pass
- [ ] Generate pass
- [ ] Qual ×3 pass
- [ ] Extended session pass
- [ ] Full loads ≤ 6
- [ ] Peak VRAM ~6 GiB class (record exact bytes)

## Export & cleanup

- [ ] Diagnostics + runtime candidate exported/committed as required
- [ ] Cost + cleanup notes recorded
- [ ] `python scripts/phase3g_cleanup_verify.py --pod-id <ID> --terminate`
- [ ] Zero remaining billable Phase resources
- [ ] Local `.ssh-*.local` / connection JSON not staged for commit
- [ ] CobraBench still `prepared-not-run`; score still **0.840**

## Pass criteria

All boxes above checked → **Outcome A** (smoke-qualified). Anything failing → stop, cleanup, do not publish a new qualified candidate without a new authorized attempt.
