#!/usr/bin/env python3
"""
Phase 3D parent: qualify Qwen3-8B on isolated Python 3.12 (.venv-qwen312).

Budget (Python 3.12 full-load subprocesses): 4
  1) initial load (no generation)
  2-4) three load+generate qualification runs

Extended session (+1 process) only after 3/3 qualification (Part 14).

Does not modify primary .venv. Does not execute CobraBench.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "evaluations/diagnostics/qwen3-8b-python-runtime-qualification"
ENV312 = ROOT / ".venv-qwen312" / "Scripts" / "python.exe"
WORKER = ROOT / "scripts" / "_qwen312_runtime_worker.py"
MANIFEST = ROOT / "model-cards/qwen/qwen3-8b.manifest.json"
INVENTORY = ROOT / "evaluations/model-inventory/qwen3-8b-local-inventory.json"
MODEL_REVISION = "b968826d9c46dd6066d109eabc6255188de91218"
MODEL_INV = "8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f"
MAX_FULL_LOADS_312 = 4
ACCESS_VIOLATION = 3221225477


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def _windows_hex(code: int | None) -> str | None:
    if code is None:
        return None
    return f"0x{(code & 0xFFFFFFFF):08X}"


def _collect_events(out: Path) -> None:
    ps = r"""
try {
  $start = (Get-Date).AddHours(-6)
  Get-WinEvent -FilterHashtable @{LogName='Application'; StartTime=$start; Level=2} -ErrorAction SilentlyContinue |
    Where-Object { $_.Message -match 'python|0xC0000005|torch_cpu|c10.dll' } |
    Select-Object -First 20 TimeCreated, Id, ProviderName, Message |
    ForEach-Object { [PSCustomObject]@{time=$_.TimeCreated.ToString('o'); id=$_.Id; provider=$_.ProviderName; message=$_.Message} } |
    ConvertTo-Json -Depth 4
} catch { @{available=$false; error=$_.Exception.Message} | ConvertTo-Json }
"""
    try:
        raw = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", ps], text=True, timeout=60
        )
        data = json.loads(raw) if raw.strip() else []
        _write(out, {"available": True, "events": data if isinstance(data, list) else [data]})
    except Exception as exc:  # noqa: BLE001
        _write(out, {"available": False, "reason": str(exc)})


def _artifact_dir() -> Path:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("model_revision") != MODEL_REVISION:
        raise RuntimeError("manifest revision mismatch")
    inv = json.loads(INVENTORY.read_text(encoding="utf-8"))
    if inv.get("inventory_hash") != MODEL_INV:
        raise RuntimeError("inventory hash mismatch")
    path = Path(data["local_artifact_root"])
    if not path.is_dir():
        raise RuntimeError(f"missing artifacts {path}")
    return path


def run_attempt(
    *,
    label: str,
    mode: str,
    full_load_count: list[int],
    enforce_ceiling: bool = True,
) -> dict:
    if enforce_ceiling and full_load_count[0] >= MAX_FULL_LOADS_312:
        raise RuntimeError("Python 3.12 full-load ceiling reached")
    attempt_id = f"py312-{label}"
    attempt_dir = DIAG / "python312" / "attempts" / attempt_id
    if attempt_dir.exists():
        raise RuntimeError(f"attempt exists: {attempt_dir}")
    attempt_dir.mkdir(parents=True)

    artifact = _artifact_dir()
    cfg = {
        "environment": "python312",
        "python_executable": str(ENV312),
        "mode": mode,
        "device_map": {"": 0},
        "quantization": "4bit-nf4-double",
        "model_revision": MODEL_REVISION,
        "model_inventory_hash": MODEL_INV,
        "benchmark": False,
    }
    _write(attempt_dir / "configuration.json", cfg)
    _write(
        attempt_dir / "smoke-input.json",
        {
            "prompt_type": "synthetic_non_benchmark",
            "keys": ["S1", "S2", "S3"],
            "notes": "Fictional evidence only; not from CobraBench.",
        },
    )

    result_json = attempt_dir / "result.json"
    progress = attempt_dir / "progress.jsonl"
    stdout = attempt_dir / "stdout.log"
    stderr = attempt_dir / "stderr.log"
    started = datetime.now(UTC).isoformat()
    cmd = [
        str(ENV312),
        str(WORKER),
        "--mode",
        mode,
        "--artifact-dir",
        str(artifact),
        "--result-json",
        str(result_json),
        "--progress-jsonl",
        str(progress),
        "--inventory-json",
        str(INVENTORY),
        "--smoke-output",
        str(attempt_dir / "smoke-output.txt"),
    ]
    with stdout.open("w", encoding="utf-8") as out_fh, stderr.open("w", encoding="utf-8") as err_fh:
        proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=out_fh, stderr=err_fh, text=True)
        pid = proc.pid
        while proc.poll() is None:
            time.sleep(5)
        code = proc.returncode
    ended = datetime.now(UTC).isoformat()
    worker = json.loads(result_json.read_text(encoding="utf-8")) if result_json.is_file() else {}
    success = code == 0 and bool(worker.get("success"))
    av = (code & 0xFFFFFFFF) == ACCESS_VIOLATION if code is not None else False
    full_load_count[0] += 1

    _collect_events(attempt_dir / "windows-event.json")
    record = {
        "schema": "cobra.diagnostics.py312_runtime_attempt.v1",
        "attempt_id": attempt_id,
        "mode": mode,
        "process_id": pid,
        "started_at": started,
        "ended_at": ended,
        "exit_code": code,
        "windows_status_code": _windows_hex(code),
        "access_violation": av,
        "success": success,
        "load_stage": worker.get("load_stage"),
        "param_device": worker.get("param_device"),
        "generation": worker.get("generation"),
        "extended": worker.get("extended"),
        "error": worker.get("error"),
        "peak_vram_bytes": worker.get("peak_vram_bytes")
        or ((worker.get("generation") or {}).get("peak_vram_bytes")),
        "full_load_index": full_load_count[0],
        "benchmark_run_created": False,
    }
    _write(attempt_dir / "attempt.json", record)
    lines = []
    for p in sorted(attempt_dir.rglob("*")):
        if p.is_file() and p.name != "sha256sums.txt":
            lines.append(f"{_sha(p)}  {p.relative_to(attempt_dir).as_posix()}")
    (attempt_dir / "sha256sums.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase",
        choices=["native-check", "initial-load", "qualify", "extended", "all"],
        default="all",
    )
    args = parser.parse_args()
    if not ENV312.is_file():
        print("missing .venv-qwen312", file=sys.stderr)
        return 2

    DIAG.mkdir(parents=True, exist_ok=True)
    (DIAG / "python312" / "attempts").mkdir(parents=True, exist_ok=True)
    manifest_path = DIAG / "manifest.json"
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.is_file()
        else {"attempts": [], "full_loads": 0}
    )
    records: list[dict] = list(manifest.get("attempts", []))
    full_loads = [int(manifest.get("full_loads", 0))]

    def persist() -> None:
        _write(
            manifest_path,
            {
                "attempts": records,
                "full_loads": full_loads[0],
                "max_full_loads_312": MAX_FULL_LOADS_312,
                "model_revision": MODEL_REVISION,
                "model_inventory_hash": MODEL_INV,
                "benchmark_executed": False,
            },
        )

    if args.phase in {"native-check", "all"}:
        _write(
            DIAG / "python312" / "native-backend-validation.json",
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "python": subprocess.check_output(
                    [str(ENV312), "-c", "import sys; print(sys.version)"], text=True
                ).strip(),
                "note": "See evaluations/environments/qwen3-8b-windows-compatibility/python312/",
            },
        )

    if args.phase in {"initial-load", "all"} and not any(r.get("mode") == "load" for r in records):
        print("==> initial-load", flush=True)
        rec = run_attempt(label="01-load", mode="load", full_load_count=full_loads)
        records.append(rec)
        persist()
        print(
            json.dumps({"success": rec["success"], "status": rec["windows_status_code"]}, indent=2)
        )
        if not rec["success"]:
            _write(
                DIAG / "python312" / "qualification_summary.json",
                {"status": "failed", "reason": "initial_load_failed"},
            )
            return 2

    if args.phase in {"qualify", "all"}:
        if not any(r.get("mode") == "load" and r.get("success") for r in records):
            print("initial load not successful; skipping qualify", flush=True)
            return 2
        existing = [r for r in records if r.get("mode") == "generate"]
        for i in range(len(existing) + 1, 4):
            if full_loads[0] >= MAX_FULL_LOADS_312:
                print("ceiling reached during qualify", flush=True)
                break
            print(f"==> qualify generate {i}/3", flush=True)
            rec = run_attempt(label=f"qual-{i:02d}", mode="generate", full_load_count=full_loads)
            records.append(rec)
            persist()
            print(
                json.dumps(
                    {"success": rec["success"], "status": rec["windows_status_code"]},
                    indent=2,
                )
            )
            if not rec["success"]:
                break

        gens = [r for r in records if r.get("mode") == "generate"]
        ok = [r for r in gens if r.get("success") and not r.get("access_violation")]
        # Require 3/3: exactly three successful generate runs and no failures among first three
        qual_status = "failed"
        if len(gens) >= 3 and all(
            r.get("success") and not r.get("access_violation") for r in gens[:3]
        ):
            qual_status = "smoke-qualified"
        elif len(ok) > 0:
            qual_status = "unstable"
        _write(
            DIAG / "python312" / "qualification_summary.json",
            {
                "status": qual_status,
                "generate_successes": len(ok),
                "generate_attempts": len(gens),
                "required": 3,
            },
        )
        print(json.dumps({"qualification": qual_status, "successes": len(ok)}, indent=2))
        if qual_status != "smoke-qualified":
            return 2

    if args.phase in {"extended", "all"}:
        qpath = DIAG / "python312" / "qualification_summary.json"
        if not qpath.is_file() or json.loads(qpath.read_text(encoding="utf-8")).get("status") != (
            "smoke-qualified"
        ):
            print("not qualified; skip extended", flush=True)
            return 2 if args.phase == "extended" else 0
        print("==> extended", flush=True)
        # Part 14: one additional load process after 3/3; do not apply the 4-ceiling
        rec = run_attempt(
            label="extended",
            mode="extended",
            full_load_count=full_loads,
            enforce_ceiling=False,
        )
        records.append(rec)
        persist()
        status = "qualified" if rec["success"] else "provisionally unstable"
        _write(DIAG / "python312" / "extended_summary.json", {"status": status, "attempt": rec})
        print(json.dumps({"extended": status}, indent=2))
        return 0 if rec["success"] else 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
