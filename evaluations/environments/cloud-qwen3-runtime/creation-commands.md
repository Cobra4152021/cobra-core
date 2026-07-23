# Cloud environment creation commands (authorized hosts only)

## Preconditions

1. `evaluations/cloud/authorization-record.json` → `authorized: true`
2. Transfer `artifacts/cloud-qwen3-runtime-qualification/cobra-core-phase3e.bundle`
3. Transfer model weights separately (never from a public bucket)

## Repository

```bash
git clone cobra-core-phase3e.bundle ~/cobra-core-cloud
cd ~/cobra-core-cloud
git checkout 695ea8833229b183e5792c49e3888ec4dde9e5f2
git rev-parse HEAD   # must equal 695ea8833229b183e5792c49e3888ec4dde9e5f2
git status --short   # must be empty
```

## Python env

```bash
python3.11 -m venv .venv-qwen-cloud
source .venv-qwen-cloud/bin/activate
python -m pip install --upgrade pip==25.1.1 setuptools==80.9.0 wheel==0.45.1
python -m pip install torch==2.6.0+cu124 --index-url https://download.pytorch.org/whl/cu124
python -m pip install -r evaluations/environments/cloud-qwen3-runtime/requirements-cloud-lock.txt
python -m pip check
```

## Model

```bash
# secure copy into ~/models/qwen3-8b/ then verify inventory hash
# required: 8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f
```

## Qualification

```bash
python scripts/qualify_qwen3_8b_cloud.py --require-authorization
# max full loads: 6; no CobraBench
```
