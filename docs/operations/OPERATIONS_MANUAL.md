# Operations Manual — Cobra Core cloud Linux runtime

**Baseline:** `phase-3f-qualified` / `0a2af49ee86451c374a600579d3644c811cd12c0`  
**Audience:** Engineer reproducing or operating the qualified Qwen3-8B cloud runtime.  
**Rules:** No model/prompt/inference changes; no CobraBench unless separately authorized; terminate resources after use.

---

## 1. First-time setup (workstation)

1. Clone this repository; checkout a commit ≥ Phase 3G P1 tooling (`85c94e5` or later) while treating **runtime equivalence** as `phase-3f-qualified`.
2. Install local Python 3.12+ for scripts/tests (workstation may be Windows).
3. Copy `.env.example` → `.env` (gitignored). Do not commit secrets.
4. Install RunPod CLI/key tooling as needed; generate or locate `runpodctl` SSH key pair under `~/.runpod/ssh/` (or `$HOME/.runpod/ssh/` on Windows).
5. Set `RUNPOD_API_KEY` in the environment (session or secret store). **Never** put it in git.
6. Ensure model weights exist locally with inventory hash  
   `8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f`  
   (weights live under `COBRA_MODEL_HOME` / transfer staging — not in git).
7. Optionally create a git bundle for air-gapped transfer:

   ```bash
   git bundle create artifacts/cloud-qwen3-runtime-qualification/cobra-core-phase3e.bundle --all
   ```

   Bundles are gitignored under `artifacts/**/*.bundle`.

8. Confirm authorization record exists and spending ceiling is understood.

---

## 2. Required environment variables

### Operator workstation

| Variable | Required | Notes |
| --- | --- | --- |
| `RUNPOD_API_KEY` | Yes for API scripts | Never print/log |
| SSH private key path | Implicit | Default runpodctl key; PasswordAuthentication off |

### Optional workstation (lab)

| Variable | Default / notes |
| --- | --- |
| `COBRA_EVAL_RESULTS_DIR` | `evaluations/results` |
| `COBRA_EVAL_REPORTS_DIR` | `evaluations/reports` |
| `COBRA_DEFAULT_SEED` | `42` |
| `COBRA_MODEL_HOME` | Local weights root (never commit) |
| Hosted provider keys | Only if using hosted APIs (not required for Phase 3F path) |

### On the GPU pod (qualification)

| Variable | Required | Example |
| --- | --- | --- |
| `COBRA_CLOUD_MODEL_DIR` | Yes | `/workspace/models/qwen3-8b` |
| `COBRA_CLOUD_INVENTORY` | Yes | `/workspace/transfer/qwen3-8b-local-inventory.json` |

---

## 3. Cloud provisioning

1. Run preflight (does **not** create pods):

   ```bash
   python scripts/phase3g_provision_preflight.py
   ```

2. Create or adopt **one** on-demand GPU pod:
   - Prefer image digest in `container-image-pin.json`
   - Prefer L4 (create) or A5000 fallback; A40 is adopt-only (see GPU docs)
   - Attach sufficient volume; plan model+venv on `/workspace`
3. Inject SSH public key / run:

   ```bash
   python scripts/phase3g_ssh_bootstrap.py --pod-id <POD_ID>
   ```

4. Confirm TCP SSH with runpodctl key works before transferring large files.

**Forbidden:** multi-GPU, spot without re-auth, public endpoints, second concurrent Phase pod.

---

## 4. Qualification workflow

Follow `docs/architecture/RUNTIME_QUALIFICATION_WORKFLOW.md` and the one-page checklist.

Summary:

```bash
# on pod
cd /workspace/cobra-core-cloud
source .venv-qwen-cloud/bin/activate
python scripts/phase3g_verify_env.py
export COBRA_CLOUD_MODEL_DIR=/workspace/models/qwen3-8b
export COBRA_CLOUD_INVENTORY=/workspace/transfer/qwen3-8b-local-inventory.json
python scripts/_phase3f_linux_qualify_parent.py
```

Expect Outcome A (6/6). Do not run CobraBench.

Detailed create commands: `evaluations/environments/cloud-qwen3-runtime/creation-commands.md`.

---

## 5. Cleanup procedure

```bash
python scripts/phase3g_cleanup_verify.py --pod-id <POD_ID> --terminate
```

Verify zero remaining billable Phase pods/volumes. See `docs/architecture/CLEANUP_WORKFLOW.md`.

---

## 6. Expected runtime (Phase 3F measured)

| Metric | Value |
| --- | --- |
| Cold full load | ~75 s |
| Subsequent loads | ~22–25 s |
| Short generate | ~1.4–9.3 s |
| Peak VRAM | ~5.88–6.32 GiB |
| Full qualification session | on the order of 1–3 h including setup (3F ≈ 3.14 h wall) |

---

## 7. Expected cloud costs

| Scenario | Estimate |
| --- | --- |
| Phase 3F actual (A40 $0.44/hr) | ~$1.38 / ~3.14 h |
| Ops-optimized session (same SKU) | ~$0.22 less setup waste per session |
| A5000 @ ~$0.25/hr (after smoke) | ~$0.19/hr cheaper vs A40 |
| Hard ceiling (3F auth) | $10 |

Always re-check live displayed $/hr before launch.

---

## 8. Troubleshooting guide

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| SSH auth fails | Missing `PUBLIC_KEY` on pod | `phase3g_ssh_bootstrap.py`; restart if required |
| `No space left on device` | Model on overlay `/` | Move to `/workspace` |
| `huggingface-hub` conflict | Wrong lock | Use `requirements-cloud-runtime.txt` (hub 1.24.0) |
| CUDA / bnb import fail | Bad image or driver | Re-pin image; confirm `nvidia-smi` |
| Load OOM | SKU &lt; 16 GB or leak | Use ≥16 GB; fresh process per qual |
| Slow first load | Cold disk + weights | Expected ~75 s; keep model on volume |
| `pip check` fails | Mixed image torch + venv | Recreate venv; install torch-pin first |
| API 401 | Bad/missing `RUNPOD_API_KEY` | Reset env; do not commit key |
| Qualify fails mid-run | Host preempt / disk | Export logs; cleanup; do not claim Outcome A |

---

## 9. Integrity reminders

- Official score remains **0.840** until a new official run is authorized.
- Protocol `prepared-not-run` for CobraBench v0.2-rc2 until authorized.
- Runtime candidate is smoke-qualified, not deployment-approved.
