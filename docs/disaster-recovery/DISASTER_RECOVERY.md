# Disaster Recovery Guide — Cobra Core

Recover the ability to operate and re-verify the **Phase 3F qualified** cloud Linux runtime after workstation loss, corrupted env, missing artifacts, or cloud-provider change.

**Invariant:** Recovery restores *ops capability* and *evidence access*. It does **not** silently change model/inference pins or official scores.

**Baseline:** `phase-3f-qualified` → `0a2af49ee86451c374a600579d3644c811cd12c0`

---

## 1. Rebuild from empty machine

1. Install Git, Python 3.12+, OpenSSH client, and (optional) RunPod CLI.
2. Clone the repository from the authoritative remote (or restore from offline git bundle).
3. Checkout tag `phase-3f-qualified` for runtime equivalence; checkout a later commit only for ops tooling (Phase 3G scripts/docs).
4. Create `.env` from `.env.example`; add secrets from a password manager (never from chat logs).
5. Recreate SSH key material for RunPod (`runpodctl` key) and register the **public** key with the provider.
6. Restore model weights from offline backup / re-download using acquisition runbooks; verify inventory hash  
   `8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f`.
7. Run local quality suite if network allows (`pytest` / project quality script) — optional for DR minimum.
8. Do **not** create cloud resources until authorization and ceiling are reconfirmed.

---

## 2. Recreate environment (pod)

Follow `evaluations/environments/cloud-qwen3-runtime/creation-commands.md`:

1. Fresh venv `.venv-qwen-cloud`
2. Install `torch-pin.json` version from cu124 index
3. Install `requirements-cloud-runtime.txt`
4. `python scripts/phase3g_verify_env.py`

If verify fails: destroy venv and recreate; do not mix image-bundled torch with partial upgrades.

---

## 3. Restore from Git bundle

On the receiving host:

```bash
git clone /path/to/cobra-core-phase3e.bundle /workspace/cobra-core-cloud
cd /workspace/cobra-core-cloud
git checkout 0a2af49ee86451c374a600579d3644c811cd12c0   # or phase-3f-qualified
test "$(git rev-parse HEAD)" = "0a2af49ee86451c374a600579d3644c811cd12c0"
```

To obtain newer ops scripts without changing runtime code, either:

- Use a newer bundle that includes Phase 3G commits, or
- `scp` only `scripts/phase3g_*.py` and env pin files onto the checkout

Do not “pip install -U” to “get unstuck.”

---

## 4. Recover qualification artifacts

| Artifact | Canonical location |
| --- | --- |
| Freeze package | `docs/releases/phase-3f/` |
| Runtime candidate | `evaluations/runtime-candidates/qwen3-8b-cloud-linux-qualified.json` (also copied under freeze) |
| Diagnostics | `evaluations/diagnostics/qwen3-8b-cloud-runtime-qualification/` + freeze copies |
| Protocol status | freeze `protocol/qwen3-8b-cobrabench-v0.2-rc2.status.json` → `prepared-not-run` |
| P1 ops evidence | `evaluations/diagnostics/phase-3g-p1/` |

If working tree is damaged but remote/tag exists: `git fetch --tags` and `git checkout phase-3f-qualified`.  
If only freeze tarball exists: restore files and verify `SHA256SUMS`.

---

## 5. Recover runtime candidate

1. Prefer git history / tag over reconstructing JSON by hand.
2. Validate fields against measured evidence (model revision, inventory hash, torch/transformers/bnb versions, `device_map`, peak VRAM).
3. If candidate file is lost but freeze package intact: copy from  
   `docs/releases/phase-3f/runtime-candidate/qwen3-8b-cloud-linux-qualified.json`.
4. Do **not** mark a new candidate `qualified` without a new Outcome A run.

---

## 6. Replace cloud provider

Provider change is a **new authorization** event.

1. Stop using old API keys; rotate/revoke.
2. Document new provider, regions, SKU list, spending ceiling, SSH method.
3. Re-pin container image digests for the new registry.
4. Recreate env from the same Python/torch/requirements pins.
5. Run abbreviated smoke (load + generate + 1 qual) minimum; full 6-load if image/CUDA stack differs.
6. Produce new evidence package; do not overwrite Phase 3F freeze in place — add a new release directory.
7. Update GPU matrix qualification status for the new host class.

---

## 7. Validation checklist

- [ ] `git rev-parse HEAD` / tag identity understood (3F vs newer ops)
- [ ] Inventory hash matches `8cf07aa8…`
- [ ] `phase3g_verify_env.py` passes on recovered venv
- [ ] Secrets present only in env / secret store
- [ ] No orphaned GPU resources from failed recovery attempts
- [ ] Freeze `SHA256SUMS` verifies if using release package
- [ ] Official score still **0.840**; protocol still `prepared-not-run` unless a later authorized phase changed them
- [ ] Runtime candidate status still `smoke-qualified` / not “deployed”

---

## 8. RTO / RPO (informal)

| Target | Expectation |
| --- | --- |
| RPO (evidence) | Git remote + tag `phase-3f-qualified` (near-zero if pushed) |
| RPO (weights) | Whatever offline/backup policy holds (weights not in git) |
| RTO (docs-only ops) | Hours to reclone + restore keys |
| RTO (re-qualify cloud) | One authorized session (~1–3 h + setup) |
