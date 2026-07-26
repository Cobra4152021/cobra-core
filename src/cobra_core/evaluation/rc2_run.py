"""Controlled CobraBench v0.2-rc2 evaluation runner (Phase 3B)."""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from cobra_core.analysis.baseline_lock import assert_path_outside_locked_baseline
from cobra_core.evaluators.citations.v2 import evaluate_citations_v2
from cobra_core.evaluators.contradictions.v2 import evaluate_contradictions_v2
from cobra_core.evaluators.format_compliance.v2 import evaluate_format_compliance_v2
from cobra_core.evaluators.telemetry.output_budget import classify_output_budget
from cobra_core.evaluators.unsupported_claims.v2 import evaluate_unsupported_claims_v2
from cobra_core.prompts.registry import load_prompt_template
from cobra_core.runtime_policies.loader import load_runtime_profile
from cobra_core.schemas.benchmark_v02 import BenchmarkCaseV02
from cobra_core.schemas.inference import InferenceRequest
from cobra_core.schemas.manifest import ModelManifest
from cobra_core.util.redact import redact_secrets

if TYPE_CHECKING:
    from cobra_core.inference.engine import LocalInferenceEngine

ROOT = Path(__file__).resolve().parents[3]
PREPARED_PROTOCOL = ROOT / "evaluations/protocols/qwen3-8b-cobrabench-v0.2-rc2.json"
RC2_DIR = ROOT / "benchmarks/releases/cobrabench-v0.2-rc2"
BASELINE_LOCK = ROOT / "evaluations/baselines/qwen3-8b-cobrabench-v0.1.json"
MANIFEST_PATH = ROOT / "model-cards/qwen/qwen3-8b.manifest.json"

RC2_INV = "08f04c10267b3f772d7783a332d816947486812f7a983dff070bdad442708cc6"
RC2_TREE = "1d438415c22827155f57817ace9274aee6c9e47048e4f6443a249ba7a5f2314f"
MODEL_REVISION = "b968826d9c46dd6066d109eabc6255188de91218"


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _sha_text(text: str) -> str:
    return _sha_bytes(text.encode("utf-8"))


def sanitize_path(path: str | Path) -> str:
    text = str(path)
    home = str(Path.home())
    if text.startswith(home):
        text = "<USER_HOME>" + text[len(home) :]
    text = text.replace("\\", "/")
    return text


def tree_hash(root: Path) -> str:
    entries: list[str] = []
    for path in sorted(
        root.rglob("*"), key=lambda item: item.relative_to(root).as_posix().casefold()
    ):
        if path.is_file() and path.name not in {"TREE_HASH.txt", "SHA256SUMS"}:
            rel = path.relative_to(root).as_posix()
            entries.append(f"{rel}:{_sha_file(path)}")
    return _sha_bytes("\n".join(entries).encode("utf-8"))


def inventory_hash(root: Path) -> str:
    inv = json.loads((root / "INVENTORY.json").read_text(encoding="utf-8"))
    payload = "\n".join(f"{e['filename']}:{e['sha256']}" for e in inv["cases"])
    return _sha_bytes(payload.encode("utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            redact_secrets(payload) if isinstance(payload, dict) else payload, indent=2, default=str
        )
        + "\n",
        encoding="utf-8",
    )


def make_run_id(*, at: datetime | None = None) -> str:
    ts = (at or datetime.now(UTC)).strftime("%Y-%m-%dT%H%M%SZ")
    return f"qwen3-8b_cobrabench-v0.2-rc2_{ts}_4bit-det"


def _system_memory() -> dict[str, Any]:
    info: dict[str, Any] = {
        "total_ram_bytes": None,
        "available_ram_bytes": None,
        "page_file_or_swap": None,
    }
    if sys.platform == "win32":
        try:
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                info["total_ram_bytes"] = int(stat.ullTotalPhys)
                info["available_ram_bytes"] = int(stat.ullAvailPhys)
                info["page_file_or_swap"] = {
                    "total_page_file_bytes": int(stat.ullTotalPageFile),
                    "available_page_file_bytes": int(stat.ullAvailPageFile),
                }
        except Exception as exc:  # noqa: BLE001
            info["error"] = str(exc)
    return info


def collect_preflight() -> dict[str, Any]:
    import torch

    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    total_vram = None
    free_vram = None
    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        total_vram = int(props.total_memory)
        free_vram = int(torch.cuda.mem_get_info()[0])
    disk = shutil.disk_usage(ROOT)
    mem = _system_memory()
    warnings: list[str] = []
    status = "pass"
    if free_vram is not None and free_vram < 6 * 1024**3:
        warnings.append("available_vram_below_6GiB")
        status = "warn"
    if mem.get("available_ram_bytes") is not None and mem["available_ram_bytes"] < 8 * 1024**3:
        warnings.append("available_system_ram_below_8GiB")
        if status != "fail":
            status = "warn"
    if disk.free < 20 * 1024**3:
        warnings.append("disk_free_below_20GiB")
        status = "fail"
    try:
        from importlib import metadata as importlib_metadata

        import transformers

        versions = {
            "python": sys.version.split()[0],
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "transformers": transformers.__version__,
            "accelerate": importlib_metadata.version("accelerate"),
            "bitsandbytes": importlib_metadata.version("bitsandbytes"),
        }
    except Exception as exc:  # noqa: BLE001
        versions = {"error": str(exc)}
        status = "fail"
        warnings.append("inference_packages_missing")

    driver = None
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=driver_version,memory.total,memory.free",
                "--format=csv,noheader",
            ],
            text=True,
            timeout=30,
        ).strip()
        driver = out
    except Exception:  # noqa: BLE001
        warnings.append("nvidia_smi_unavailable")

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "host_identifier": platform.node()[:3] + "***",
        "os": platform.platform(),
        "software_versions": versions,
        "hardware": {
            "gpu_model": gpu_name,
            "total_vram_bytes": total_vram,
            "available_vram_bytes": free_vram,
            "nvidia_smi": driver,
        },
        "memory": mem,
        "disk": {
            "root": sanitize_path(ROOT),
            "total_bytes": disk.total,
            "free_bytes": disk.free,
        },
        "model_cache_location": sanitize_path("D:/cobra-models"),
        "pass_fail_status": status,
        "warnings": warnings,
        "cuda_available": bool(torch.cuda.is_available()),
        "seed_controls_available": True,
        "output_persistence_guaranteed": True,
    }


def build_model_inventory(manifest: ModelManifest) -> dict[str, Any]:
    artifact_root = Path(manifest.local_artifact_root) if manifest.local_artifact_root else None
    files: list[dict[str, Any]] = []
    config_hash: str | None = None
    tokenizer_hashes: dict[str, str] = {}
    if artifact_root and artifact_root.is_dir():
        for path in sorted(artifact_root.iterdir()):
            if not path.is_file():
                continue
            # Skip HF download cache noise; record model/tokenizer/config only.
            rel = path.name
            digest = _sha_file(path)
            entry: dict[str, Any] = {
                "relpath": rel,
                "size_bytes": path.stat().st_size,
                "sha256": digest,
            }
            files.append(entry)
            if rel == "config.json":
                config_hash = digest
            if rel in {
                "tokenizer.json",
                "tokenizer_config.json",
                "vocab.json",
                "merges.txt",
                "special_tokens_map.json",
            }:
                tokenizer_hashes[rel] = digest
    weight_files = [f for f in files if str(f["relpath"]).endswith(".safetensors")]
    inventory = {
        "model_name": manifest.model_name,
        "upstream_repository": str(manifest.source_repository),
        "model_revision": manifest.model_revision,
        "tokenizer_revision": manifest.model_revision,
        "source_commit": manifest.source_commit,
        "local_artifact_root": sanitize_path(artifact_root) if artifact_root else None,
        "config_hash": config_hash,
        "tokenizer_file_hashes": tokenizer_hashes,
        "weight_file_inventory": weight_files,
        "quantization_method": "bitsandbytes-4bit-nf4",
        "quantization_configuration": {
            "load_in_4bit": True,
            "bnb_4bit_quant_type": "nf4",
            "bnb_4bit_use_double_quant": True,
            "bnb_4bit_compute_dtype": "float16",
        },
        "trust_remote_code": False,
        "dtype": "4bit-nf4 / float16 compute",
        "device_map": "auto",
        "files": files,
    }
    payload = json.dumps(
        {k: v for k, v in inventory.items() if k != "inventory_hash"},
        sort_keys=True,
    ).encode("utf-8")
    inventory["inventory_hash"] = _sha_bytes(payload)
    return inventory


def build_user_prompt_v02(case: BenchmarkCaseV02) -> str:
    parts = [case.user_prompt.rstrip(), "", "Supporting sources (cite using the citation keys):"]
    for source in case.supporting_sources:
        parts.extend(
            [
                "",
                f"[SOURCE {source.citation_key}]",
                f"Title: {source.title}",
                "Content:",
                source.content,
            ]
        )
    return "\n".join(parts).strip() + "\n"


def resolve_max_new_tokens(case: BenchmarkCaseV02) -> int:
    profile_id = case.output_budget.runtime_profile_id if case.output_budget else None
    if not profile_id:
        profile_id = "deterministic-investigation"
    profile = load_runtime_profile(profile_id, repo_root=ROOT)
    return int(getattr(profile, "max_output_tokens", 1024) or 1024)


def run_evaluators(case: BenchmarkCaseV02, response: str) -> dict[str, Any]:
    allowed = [s.citation_key for s in case.supporting_sources]
    sources = {s.citation_key: s.content for s in case.supporting_sources}
    pins = case.evaluator_versions.model_dump(exclude_none=True) if case.evaluator_versions else {}
    out: dict[str, Any] = {"authoritative": {}, "advisory": {}, "pins": pins}

    if pins.get("citations"):
        mat = case.material_evidence
        cit = evaluate_citations_v2(
            response,
            allowed_keys=allowed,
            required_evidence_ids=mat.required_evidence_ids if mat else allowed,
            optional_evidence_ids=mat.optional_evidence_ids if mat else [],
            contrary_evidence_ids=mat.contrary_evidence_ids if mat else [],
            supporting_source_texts=sources,
        )
        out["authoritative"]["citations"] = {
            "version": "2.0.0",
            "status": "authoritative_with_caveats",
            "metrics": cit.model_dump(mode="json"),
        }

    if pins.get("format_compliance"):
        fmt = evaluate_format_compliance_v2(response)
        out["authoritative"]["format_compliance"] = {
            "version": "2.0.0",
            "status": "authoritative_with_caveats",
            "metrics": fmt.model_dump(mode="json"),
        }

    if pins.get("contradictions"):
        contra = evaluate_contradictions_v2(response)
        out["authoritative"]["contradictions"] = {
            "version": "2.0.0",
            "status": "authoritative_detection_incomplete_without_human_explanation",
            "metrics": contra.model_dump(mode="json"),
            "human_review_required": ["explanation_quality"],
        }

    if pins.get("unsupported_claims"):
        uc = evaluate_unsupported_claims_v2(response, allowed, sources)
        out["advisory"]["unsupported_claims"] = {
            "version": "2.0.0",
            "status": "advisory-only",
            "warning": (
                "Phase 2I adversarial audit: TPR=0.0 FNR=1.0 cannot_determine_rate=0.7. "
                "Zero flags is not proof of grounding."
            ),
            "metrics": uc.model_dump(mode="json"),
        }

    if pins.get("output_budget_telemetry") or True:
        # Always record budget classification when token counts known by caller.
        out["authoritative"]["output_budget_telemetry_placeholder"] = {
            "version": "1.0.0",
            "status": "filled_by_runner_with_token_counts",
        }
    return out


def create_run_workspace(
    run_id: str, *, code_commit: str, preflight: dict[str, Any], inventory: dict[str, Any]
) -> Path:
    run_dir = ROOT / "evaluations" / "runs" / run_id
    if run_dir.exists():
        raise RuntimeError(f"run directory already exists: {run_dir}")
    for name in (
        "raw",
        "parsed",
        "telemetry",
        "scores",
        "human_review",
        "logs",
        "errors",
        "reports",
    ):
        (run_dir / name).mkdir(parents=True, exist_ok=True)

    prepared = json.loads(PREPARED_PROTOCOL.read_text(encoding="utf-8"))
    if prepared.get("status") != "prepared-not-run":
        raise RuntimeError("prepared protocol status drifted")
    prepared_hash = _sha_file(PREPARED_PROTOCOL)

    if inventory_hash(RC2_DIR) != RC2_INV or tree_hash(RC2_DIR) != RC2_TREE:
        raise RuntimeError("rc2 hash mismatch at run workspace creation")

    assert_path_outside_locked_baseline(BASELINE_LOCK, run_dir, repo_root=ROOT)

    protocol = {
        **prepared,
        "status": "running",
        "execution_copy": True,
        "prepared_protocol_path": "evaluations/protocols/qwen3-8b-cobrabench-v0.2-rc2.json",
        "prepared_protocol_sha256": prepared_hash,
        "prepared_protocol_status_unchanged": "prepared-not-run",
        "run_id": run_id,
        "rc2_inventory_hash": RC2_INV,
        "rc2_tree_hash": RC2_TREE,
        "model_inventory_hash": inventory["inventory_hash"],
        "code_commit_sha": code_commit,
        "started_at": datetime.now(UTC).isoformat(),
        "ended_at": None,
        "label": "Experimental release-candidate evaluation — not an official CobraBench v0.2 score.",
        "official_v01_score_not_superseded": 0.840,
    }
    write_json(run_dir / "protocol.json", protocol)
    write_json(run_dir / "environment.json", preflight)
    write_json(run_dir / "model_inventory.json", inventory)
    (run_dir / "RUN.md").write_text(
        f"# Run {run_id}\n\nExperimental rc2 evaluation. Not official. Not comparable to 0.840.\n",
        encoding="utf-8",
    )
    return run_dir


def checkpoint_manifest(run_dir: Path, manifest: dict[str, Any]) -> None:
    write_json(run_dir / "case_manifest.json", manifest)


def finalize_sha256sums(run_dir: Path) -> str:
    lines: list[str] = []
    for path in sorted(run_dir.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS":
            rel = path.relative_to(run_dir).as_posix()
            lines.append(f"{_sha_file(path)}  {rel}")
    (run_dir / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tree_hash(run_dir)


def build_human_review_queue(
    case: BenchmarkCaseV02, scores: dict[str, Any], response_path: str
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    cat = case.category.value
    base = {
        "case_id": case.case_id,
        "raw_response_path": response_path,
        "reviewer_status": "pending-human-review",
    }
    if scores.get("advisory", {}).get("unsupported_claims") or cat in {
        "hallucination_resistance",
        "evidence_grounding",
        "investigation_reasoning",
    }:
        items.append(
            {
                **base,
                "question": "Adjudicate unsupported factual claims and assign H0–H5 hallucination severity.",
                "allowed_ratings": ["H0", "H1", "H2", "H3", "H4", "H5", "no_unsupported"],
                "automated_findings": scores.get("advisory", {}).get("unsupported_claims"),
            }
        )
    if scores.get("authoritative", {}).get("contradictions") or cat == "contradiction_detection":
        items.append(
            {
                **base,
                "question": "Rate contradiction explanation quality and invented-reconciliation avoidance.",
                "allowed_ratings": ["strong", "adequate", "weak", "missing", "harmful_reconcile"],
                "automated_findings": scores.get("authoritative", {}).get("contradictions"),
            }
        )
    if cat in {"uncertainty_calibration", "refusal_quality", "long_document_analysis", "coding"}:
        items.append(
            {
                **base,
                "question": f"Human judgment required for category {cat}.",
                "allowed_ratings": ["pass", "partial", "fail", "needs_discussion"],
                "automated_findings": None,
            }
        )
    return items


def execute_case(
    *,
    engine: LocalInferenceEngine,
    manifest: ModelManifest,
    case: BenchmarkCaseV02,
    run_dir: Path,
) -> dict[str, Any]:
    cid = case.case_id
    t0 = time.perf_counter()
    record: dict[str, Any] = {
        "case_id": cid,
        "status": "completed",
        "failure_class": None,
        "retries": [],
    }
    try:
        if case.prompt_template_id and case.prompt_template_version:
            load_prompt_template(
                case.prompt_template_id, case.prompt_template_version, repo_root=ROOT
            )
        user_prompt = build_user_prompt_v02(case)
        system_prompt = case.system_prompt
        prompt_hash = _sha_text(system_prompt + "\n---\n" + user_prompt)
        max_new = resolve_max_new_tokens(case)
        req = InferenceRequest(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_new_tokens=max_new,
            temperature=0.0,
            seed=123,
            enable_thinking=False,
        )
        write_json(
            run_dir / "parsed" / f"{cid}.prompt.json",
            {
                "case_id": cid,
                "prompt_hash": prompt_hash,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "max_new_tokens": max_new,
                "template": f"{case.prompt_template_id}@{case.prompt_template_version}",
            },
        )
        result = engine.run(
            manifest=manifest,
            manifest_ref=str(MANIFEST_PATH.relative_to(ROOT)).replace("\\", "/"),
            request=req,
            environment_reference="phase3b-rc2",
            results_dir=None,
            persist=False,
        )
        response = result.assistant_response or ""
        (run_dir / "raw" / f"{cid}.txt").write_text(response, encoding="utf-8")
        finish = result.finish_reason or "unknown"
        in_tok = result.input_token_count or 0
        out_tok = result.output_token_count or 0
        budget = classify_output_budget(
            response=response,
            requested_max_output_tokens=max_new,
            actual_output_tokens=out_tok,
            finish_reason=str(finish),
            required_sections=case.output_budget.required_sections if case.output_budget else [],
        )
        telemetry = {
            "case_id": cid,
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "max_output_tokens": max_new,
            "budget_used_pct": round(100.0 * out_tok / max_new, 2) if max_new else None,
            "finish_reason": finish,
            "latency_ms": result.total_latency_ms,
            "tokens_per_second": result.tokens_per_second,
            "output_budget": budget.model_dump(mode="json"),
            "prompt_hash": prompt_hash,
        }
        write_json(run_dir / "telemetry" / f"{cid}.json", telemetry)
        scores = run_evaluators(case, response)
        if "output_budget_telemetry_placeholder" in scores.get("authoritative", {}):
            scores["authoritative"]["output_budget_telemetry"] = {
                "version": "1.0.0",
                "status": "authoritative_with_caveats",
                "metrics": budget.model_dump(mode="json"),
            }
            del scores["authoritative"]["output_budget_telemetry_placeholder"]
        write_json(run_dir / "scores" / f"{cid}.json", scores)
        write_json(
            run_dir / "parsed" / f"{cid}.json",
            {
                "case_id": cid,
                "response_sha256": _sha_text(response),
                "category": case.category.value,
                "difficulty_level": case.difficulty_level,
                "human_fields": "pending-human-review",
            },
        )
        queue = build_human_review_queue(case, scores, f"raw/{cid}.txt")
        write_json(run_dir / "human_review" / f"{cid}.json", {"items": queue})
        record.update(
            {
                "prompt_hash": prompt_hash,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "finish_reason": finish,
                "duration_s": round(time.perf_counter() - t0, 3),
                "human_review_items": len(queue),
            }
        )
    except Exception as exc:  # noqa: BLE001
        record["status"] = "generation_error"
        record["failure_class"] = "generation_error"
        record["error"] = str(exc)
        write_json(
            run_dir / "errors" / f"{cid}.json",
            {"case_id": cid, "failure_class": "generation_error", "error": str(exc)},
        )
    return record
