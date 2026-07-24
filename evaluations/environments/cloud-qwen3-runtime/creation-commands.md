# Cloud environment creation commands (authorized hosts only)

Phase 3G P1 reproducible setup. Preserves Phase 3F qualified pins (`phase-3f-qualified`).

## Preconditions

1. `evaluations/cloud/authorization-record.json` → `authorized: true`
2. Prefer image pin in `container-image-pin.json`
3. Transfer git bundle + model weights over SSH (never public bucket)
4. Use `/workspace` (or network volume) for repo, venv, and model

## SSH bootstrap (from operator workstation)

```bash
# Ensure RUNPOD_API_KEY is set in the environment (do not print it)
python scripts/phase3g_ssh_bootstrap.py --pod-id <POD_ID>
# On success, writes evaluations/cloud/.ssh-method.local.json (gitignored locally)
```

## Repository

```bash
# On the pod — paths under /workspace
mkdir -p /workspace/transfer /workspace/models
# after scp of cobra-core-phase3e.bundle:
git clone /workspace/transfer/cobra-core-phase3e.bundle /workspace/cobra-core-cloud
cd /workspace/cobra-core-cloud
git checkout 695ea8833229b183e5792c49e3888ec4dde9e5f2
test "$(git rev-parse HEAD)" = "695ea8833229b183e5792c49e3888ec4dde9e5f2"
```

For Phase 3G tooling that post-dates the bundle commit, sync the needed scripts/locks via scp after checkout (do not change model/inference code).

## Python env (runtime)

```bash
cd /workspace/cobra-core-cloud
python3.12 -m venv .venv-qwen-cloud   # 3.11 also OK; not 3.13
source .venv-qwen-cloud/bin/activate
python -m pip install --upgrade pip==25.1.1 setuptools==80.9.0 wheel==0.45.1
python -m pip install torch==2.6.0+cu124 --index-url https://download.pytorch.org/whl/cu124
python -m pip install -r evaluations/environments/cloud-qwen3-runtime/requirements-cloud-runtime.txt
python -m pip check
python scripts/phase3g_verify_env.py
```

Optional (tests only):

```bash
python -m pip install -r evaluations/environments/cloud-qwen3-runtime/requirements-cloud-dev.txt
```

## Model

```bash
# scp/tar into /workspace/models/qwen3-8b/
# required inventory hash:
# 8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f
```

## Qualification (smoke only; no CobraBench)

```bash
export COBRA_CLOUD_MODEL_DIR=/workspace/models/qwen3-8b
export COBRA_CLOUD_INVENTORY=/workspace/transfer/qwen3-8b-local-inventory.json
python scripts/_phase3f_linux_qualify_parent.py
# max full loads: 6; no CobraBench
```

## Cleanup

```bash
# From operator workstation after export:
python scripts/phase3g_cleanup_verify.py --pod-id <POD_ID> --terminate
```
