#!/usr/bin/env python3
"""Generate Phase 3F cloud preparation artifacts (no provisioning, no spend)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQ_COMMIT = "695ea8833229b183e5792c49e3888ec4dde9e5f2"
MODEL_REV = "b968826d9c46dd6066d109eabc6255188de91218"
MODEL_INV = "8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f"
BUNDLE_DIR = ROOT / "artifacts/cloud-qwen3-runtime-qualification"
BUNDLE = BUNDLE_DIR / "cobra-core-phase3e.bundle"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def write_json(path: Path, data: object) -> None:
    write(path, json.dumps(data, indent=2))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    write_json(
        ROOT / "evaluations/cloud/authorization-record.json",
        {
            "schema": "cobra.cloud.authorization.v1",
            "status": "ready-for-cloud-authorization",
            "authorized": False,
            "provider": None,
            "instance_type": None,
            "gpu": None,
            "quoted_hourly_rate_usd": None,
            "approved_spending_ceiling_usd": None,
            "approved_runtime_ceiling_hours": None,
            "approved_disk_size_gb": None,
            "region": None,
            "authorization_timestamp": None,
            "authorization_source": None,
            "rules": {
                "max_active_gpu_instances": 1,
                "max_persistent_volumes": 1,
                "autoscaling": False,
                "multi_node": False,
                "managed_endpoint": False,
                "public_inference_service": False,
                "reserved_commitment": False,
                "automatic_recurring_charges": False,
            },
            "notes": (
                "Phase 3F Gate 2: user must explicitly authorize provider, GPU, "
                "spending limit, max runtime, storage size, and region before any provisioning."
            ),
            "payment_information_recorded": False,
        },
    )

    write_json(
        ROOT / "evaluations/cloud/security-manifest.json",
        {
            "schema": "cobra.cloud.security_manifest.v1",
            "status": "planned-not-provisioned",
            "ports_opened": [],
            "authentication_method": "ssh-key-preferred-when-authorized",
            "password_authentication": "disabled-when-key-auth-available",
            "storage_encryption_status": "require-provider-encryption-when-available",
            "public_ip_status": "not_provisioned",
            "firewall_or_security_group_summary": (
                "deny-all-inbound-except-ssh-from-authorized-sources"
            ),
            "secrets_used_by_category": [],
            "cleanup_requirements": [
                "terminate_gpu_instance",
                "delete_temporary_volumes",
                "delete_temporary_object_storage",
                "revoke_temporary_credentials",
                "confirm_no_managed_endpoint",
                "confirm_no_recurring_jobs",
            ],
            "prohibited": [
                "public_jupyter",
                "tokens_in_source",
                "commit_secrets",
                "api_keys_in_artifacts",
                "private_ssh_keys_in_repo",
                "billing_identifiers",
                "access_tokens",
            ],
            "contains_secrets": False,
        },
    )

    write_json(
        ROOT / "evaluations/cloud/cost-record.json",
        {
            "schema": "cobra.cloud.cost_record.v1",
            "status": "no_spend",
            "provider": None,
            "redacted_instance_class": None,
            "gpu_model": None,
            "hourly_rate_at_launch_usd": None,
            "storage_rate_usd": None,
            "launch_timestamp": None,
            "termination_timestamp": None,
            "billed_or_estimated_duration_hours": 0,
            "estimated_compute_cost_usd": 0,
            "estimated_storage_cost_usd": 0,
            "total_estimated_cost_usd": 0,
            "approved_spending_ceiling_usd": None,
            "ceiling_respected": True,
            "notes": "No instance created; Outcome H.",
        },
    )

    write_json(
        ROOT / "evaluations/cloud/cleanup-verification.json",
        {
            "schema": "cobra.cloud.cleanup_verification.v1",
            "status": "not_applicable_no_instance",
            "instance_terminated": True,
            "volume_deleted_or_retained_by_authorization": "n/a",
            "temporary_uploads_deleted": True,
            "credentials_revoked": True,
            "public_services_absent": True,
            "remaining_billable_resources": [],
            "verification_timestamp": None,
            "notes": "No cloud resources were provisioned in Phase 3F preparation.",
        },
    )

    write_json(
        ROOT / "evaluations/cloud/export-verification.json",
        {
            "schema": "cobra.cloud.export_verification.v1",
            "status": "preparation_only",
            "files_expected": [
                "artifacts/cloud-qwen3-runtime-qualification/cobra-core-phase3e.bundle",
                "artifacts/cloud-qwen3-runtime-qualification/cloud-transfer-manifest.json",
                "evaluations/cloud/authorization-record.json",
                "evaluations/cloud/security-manifest.json",
            ],
            "files_received": [],
            "file_hashes": {},
            "missing_files": [],
            "verification_status": "local_preparation_complete",
            "notes": "Cloud export verification deferred until an authorized instance exists.",
        },
    )

    lock_lines = [
        "# Proposed cloud Linux lock for Phase 3F (NOT installed on this host).",
        "# Python 3.11 preferred; 3.12 acceptable. Do not use Python 3.13.",
        "# Install torch from official cu124 wheel index when authorized.",
        "pip==25.1.1",
        "setuptools==80.9.0",
        "wheel==0.45.1",
        "numpy==2.2.6",
        "psutil==7.0.0",
        "pytest==8.4.1",
        "safetensors==0.5.3",
        "tokenizers==0.22.1",
        "huggingface-hub==0.34.4",
        "transformers==5.14.1",
        "accelerate==1.14.0",
        "bitsandbytes==0.49.2",
        "# torch==2.6.0+cu124  # install separately from https://download.pytorch.org/whl/cu124",
    ]
    lock_text = "\n".join(lock_lines) + "\n"
    lock_path = ROOT / "evaluations/environments/cloud-qwen3-runtime/requirements-cloud-lock.txt"
    write(lock_path, lock_text)
    lock_hash = hashlib.sha256(lock_text.encode("utf-8")).hexdigest()
    write(
        ROOT / "evaluations/environments/cloud-qwen3-runtime/dependency-lock.sha256",
        lock_hash + "  requirements-cloud-lock.txt\n",
    )

    write_json(
        ROOT / "evaluations/environments/cloud-qwen3-runtime/environment-manifest.json",
        {
            "schema": "cobra.cloud.environment_manifest.v1",
            "status": "prepared-not-provisioned",
            "preferred_python": "3.11",
            "acceptable_python": ["3.11", "3.12"],
            "prohibited_python": ["3.13"],
            "venv_path": "~/cobra-core-cloud/.venv-qwen-cloud/",
            "requirements_lock": "requirements-cloud-lock.txt",
            "dependency_lock_sha256": lock_hash,
            "torch_install_note": (
                "Install exact torch==2.6.0+cu124 (or driver-compatible stable cu12x wheel) "
                "from official PyTorch index; no nightlies; no source builds."
            ),
            "prohibited_packages": [
                "flash-attn",
                "xformers",
                "deepspeed",
                "vllm",
                "llama-cpp-python",
            ],
            "quantization": {
                "load_in_4bit": True,
                "bnb_4bit_quant_type": "nf4",
                "bnb_4bit_use_double_quant": True,
                "bnb_4bit_compute_dtype": "float16",
            },
            "device_map": {"": 0},
            "model_revision": MODEL_REV,
            "model_inventory_hash": MODEL_INV,
            "required_repo_commit": REQ_COMMIT,
        },
    )

    write(
        ROOT / "evaluations/environments/cloud-qwen3-runtime/README.md",
        """# Cloud Qwen3-8B runtime (Phase 3F)

Status: **prepared-not-provisioned** (Outcome H — awaiting cloud authorization).

Do not create an instance until `evaluations/cloud/authorization-record.json` has
`authorized: true` with provider, GPU, spending ceiling, runtime ceiling, disk size, and region.

See `creation-commands.md` and `selection-rationale.md`.
""",
    )

    write(
        ROOT / "evaluations/environments/cloud-qwen3-runtime/creation-commands.md",
        f"""# Cloud environment creation commands (authorized hosts only)

## Preconditions

1. `evaluations/cloud/authorization-record.json` → `authorized: true`
2. Transfer `artifacts/cloud-qwen3-runtime-qualification/cobra-core-phase3e.bundle`
3. Transfer model weights separately (never from a public bucket)

## Repository

```bash
git clone cobra-core-phase3e.bundle ~/cobra-core-cloud
cd ~/cobra-core-cloud
git checkout {REQ_COMMIT}
git rev-parse HEAD   # must equal {REQ_COMMIT}
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
# required: {MODEL_INV}
```

## Qualification

```bash
python scripts/qualify_qwen3_8b_cloud.py --require-authorization
# max full loads: 6; no CobraBench
```
""",
    )

    write(
        ROOT / "evaluations/environments/cloud-qwen3-runtime/selection-rationale.md",
        """# Dependency selection rationale (proposed)

| Package | Version | Why |
| --- | --- | --- |
| Python | 3.11 (pref) / 3.12 | Stable scientific wheels; avoid 3.13 after Windows instability |
| torch | 2.6.0+cu124 | Matches validated micro-op stack; official Linux wheel |
| transformers | 5.14.1 | Qwen3 support; pinned for reproducibility |
| accelerate | 1.14.0 | Explicit device_map support |
| bitsandbytes | 0.49.2 | 4-bit NF4 path used in prior phases |
| numpy | 2.2.6 | Has cp311/cp312 wheels; conservative |
| safetensors / tokenizers / huggingface-hub | pinned | Load path integrity |
| psutil / pytest | pinned | Telemetry and tests |

No FlashAttention, xFormers, DeepSpeed, vLLM, or source builds in Phase 3F first qualification.
""",
    )

    for name in ("pip-freeze.txt", "pip-check.txt"):
        write(
            ROOT / f"evaluations/environments/cloud-qwen3-runtime/{name}",
            "# Not created — awaiting authorized cloud host (Outcome H).\n",
        )

    write_json(
        ROOT / "evaluations/environments/cloud-qwen3-runtime/native-library-inventory.json",
        {
            "status": "not_collected",
            "reason": "no_cloud_host",
            "libraries": [],
            "native_library_inventory_hash": None,
        },
    )

    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)
    write_json(
        BUNDLE_DIR / "synthetic-smoke-prompts.json",
        {
            "benchmark_content": False,
            "initial_generation": {
                "evidence": [
                    "[S1] The shipment was logged at 08:40.",
                    "[S2] The inspection form was signed at 09:05.",
                    "[S3] No record identifies who moved the shipment.",
                ],
                "instruction": (
                    "List the supported facts, identify the unresolved uncertainty, "
                    "cite only S1/S2/S3."
                ),
            },
            "qualification": "reuse_same_style_fictional_evidence_not_from_CobraBench",
            "extended_session_prompts": 5,
        },
    )
    write(
        BUNDLE_DIR / "EXECUTION.md",
        f"""# Cloud qualification execution (after authorization)

1. Confirm `evaluations/cloud/authorization-record.json` authorized fields are complete.
2. Provision **one** Linux GPU host (≥16 GB VRAM; prefer 24 GB).
3. Transfer this directory + model weights via encrypted private channel.
4. Clone bundle → `~/cobra-core-cloud` at `{REQ_COMMIT}`.
5. Verify frozen hashes and protocol `prepared-not-run`.
6. Verify model inventory `{MODEL_INV}`.
7. Create `.venv-qwen-cloud` and install pinned deps.
8. Run native backend validation; stop on failure.
9. Run `scripts/qualify_qwen3_8b_cloud.py` (max 6 full loads).
10. Export artifacts; verify locally; terminate instance; fill cost/cleanup records.

Do **not** execute CobraBench in Phase 3F.
""",
    )
    write(
        BUNDLE_DIR / "CLEANUP.md",
        """# Cleanup checklist

- [ ] Stop qualification processes
- [ ] Terminate GPU instance
- [ ] Delete temporary volumes (unless retention authorized)
- [ ] Delete temporary object-storage uploads
- [ ] Revoke temporary credentials
- [ ] Confirm no managed endpoint / recurring job / unauthorized snapshot
- [ ] Update `evaluations/cloud/cleanup-verification.json`
- [ ] Update `evaluations/cloud/cost-record.json`
""",
    )
    write(
        BUNDLE_DIR / "README.md",
        """# Cloud Qwen3-8B runtime qualification transfer package

Phase 3F preparation package. **No cloud spend authorized yet.**

Contents include the Git bundle at Phase 3E commit, model inventory checksums (not weights),
synthetic prompts, and execution/cleanup instructions.

Regenerate the bundle with:

```bash
git bundle create artifacts/cloud-qwen3-runtime-qualification/cobra-core-phase3e.bundle --all
```
""",
    )
    write_json(
        BUNDLE_DIR / "expected-artifact-schemas.json",
        {
            "attempt_files": [
                "attempt.json",
                "configuration.json",
                "stdout.log",
                "stderr.log",
                "memory.jsonl",
                "gpu.jsonl",
                "kernel-events.txt",
                "result.json",
                "smoke-input.json",
                "smoke-output.txt",
                "sha256sums.txt",
            ],
            "max_full_loads": 6,
            "qualification_required": 3,
            "extended_prompts": 5,
            "model_revision": MODEL_REV,
            "model_inventory_hash": MODEL_INV,
            "required_repo_commit": REQ_COMMIT,
        },
    )

    entries = []
    for p in (
        BUNDLE,
        BUNDLE_DIR / "model-inventory.json",
        BUNDLE_DIR / "model-file-integrity.json",
        BUNDLE_DIR / "synthetic-smoke-prompts.json",
        BUNDLE_DIR / "expected-artifact-schemas.json",
        BUNDLE_DIR / "EXECUTION.md",
        BUNDLE_DIR / "CLEANUP.md",
        BUNDLE_DIR / "README.md",
    ):
        if not p.is_file():
            continue
        entries.append(
            {
                "path": p.as_posix().replace("\\", "/"),
                "size_bytes": p.stat().st_size,
                "sha256": sha256_file(p),
            }
        )

    manifest = {
        "schema": "cobra.cloud.transfer_manifest.v1",
        "source_commit": REQ_COMMIT,
        "status": "ready-for-cloud-authorization",
        "included": entries,
        "excluded": [
            ".venv*",
            "**/__pycache__/",
            "**/*.safetensors",
            "D:/cobra-models/**",
            "secrets/",
            "*.pem",
            "*.key",
            "evaluations/runs/**",
        ],
        "total_bundle_size_bytes": sum(e["size_bytes"] for e in entries),
        "model_weights_included": False,
        "model_transfer": "separate_encrypted_copy_of_validated_local_artifacts",
        "model_revision": MODEL_REV,
        "model_inventory_hash": MODEL_INV,
    }
    write_json(BUNDLE_DIR / "cloud-transfer-manifest.json", manifest)
    write_json(ROOT / "evaluations/cloud/cloud-transfer-manifest.json", manifest)

    write_json(
        ROOT / "evaluations/diagnostics/qwen3-8b-cloud-runtime-qualification/OUTCOME.json",
        {
            "phase": "3F",
            "outcome": "H",
            "outcome_label": "Qualification prepared but no cloud spending authorized",
            "status": "ready-for-cloud-authorization",
            "authorized": False,
            "instance_count": 0,
            "full_load_attempts": 0,
            "successful_loads": 0,
            "successful_generations": 0,
            "segmentation_faults": 0,
            "oom_kills": 0,
            "caught_cuda_errors": 0,
            "runtime_candidate_created": False,
            "benchmark_executed": False,
            "prepared_protocol_status": "prepared-not-run",
            "official_v01_score_unchanged": 0.84,
            "required_repo_commit": REQ_COMMIT,
            "model_revision": MODEL_REV,
            "model_inventory_hash": MODEL_INV,
            "transfer_bundle": "artifacts/cloud-qwen3-runtime-qualification/",
            "git_bundle_sha256": sha256_file(BUNDLE) if BUNDLE.is_file() else None,
            "total_estimated_cost_usd": 0,
            "remaining_billable_resources": [],
            "next_authorized_phase": (
                "Await explicit cloud authorization, then provision one approved GPU host"
            ),
        },
    )
    write_json(
        ROOT / "evaluations/diagnostics/qwen3-8b-cloud-runtime-qualification/manifest.json",
        {
            "phase": "3F",
            "schema": "cobra.diagnostics.cloud_runtime_qualification.v1",
            "max_full_loads": 6,
            "full_loads_executed": 0,
            "attempts": [],
            "blocked_at_gate": 2,
            "block_reason": "no_cloud_authorization",
            "benchmark_executed": False,
            "model_revision": MODEL_REV,
            "model_inventory_hash": MODEL_INV,
            "required_repo_commit": REQ_COMMIT,
            "outcome": "H",
        },
    )
    write_json(
        ROOT / "evaluations/diagnostics/qwen3-8b-cloud-runtime-qualification/environment.json",
        {"status": "not_provisioned", "provider": None, "gpu": None},
    )

    diag = ROOT / "evaluations/diagnostics/qwen3-8b-cloud-runtime-qualification"
    lines = []
    for p in sorted(diag.rglob("*")):
        if p.is_file() and p.name != "SHA256SUMS":
            rel = p.relative_to(diag).as_posix()
            lines.append(f"{sha256_file(p)}  {rel}")
    write(diag / "SHA256SUMS", "\n".join(lines) + "\n")

    print("bundle", sha256_file(BUNDLE) if BUNDLE.is_file() else None)
    print("lock", lock_hash)
    print("entries", len(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
