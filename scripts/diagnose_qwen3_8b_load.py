#!/usr/bin/env python3
"""
Phase 3C parent orchestrator: subprocess-isolated Qwen3-8B load diagnostics.

Does not execute CobraBench. Does not mutate the prepared rc2 protocol.
Maximum live load attempts: 6.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.diagnostics.load_isolation import (  # noqa: E402
    CONFIGS,
    DIAG_ROOT,
    MAX_LIVE_LOAD_ATTEMPTS,
    attempt_schema,
    classify_qualification,
    count_live_loads,
    nvidia_smi_snapshot,
    system_memory,
    write_json,
)

WORKER = ROOT / "scripts" / "_qwen3_8b_load_worker.py"
PYTHON = Path(sys.executable)


def _host_readiness(path: Path) -> dict:
    import shutil

    disk = shutil.disk_usage(ROOT)
    snap = {
        "timestamp": datetime.now(UTC).isoformat(),
        "nvidia_smi": nvidia_smi_snapshot(),
        "memory": system_memory(),
        "disk": {"total_bytes": disk.total, "free_bytes": disk.free},
        "python": sys.version,
        "executable": str(PYTHON),
    }
    # Process list (names only)
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-compute-apps=pid,process_name,used_memory",
                "--format=csv,noheader",
            ],
            text=True,
            timeout=30,
        ).strip()
        snap["compute_apps"] = out.splitlines() if out else []
    except Exception as exc:  # noqa: BLE001
        snap["compute_apps_error"] = str(exc)
    write_json(path, snap)
    return snap


def _collect_windows_events(out_path: Path) -> dict:
    """Best-effort Application Error events (last 24h). Does not require debugger install."""
    if sys.platform != "win32":
        payload = {"available": False, "reason": "not_windows"}
        write_json(out_path, payload)
        return payload
    ps = r"""
$ErrorActionPreference = 'Stop'
try {
  $start = (Get-Date).AddHours(-24)
  $events = Get-WinEvent -FilterHashtable @{LogName='Application'; StartTime=$start; Level=2} -ErrorAction SilentlyContinue |
    Where-Object { $_.ProviderName -match 'Windows Error Reporting|Application Error' -or $_.Message -match 'python|0xC0000005|ACCESS_VIOLATION' } |
    Select-Object -First 40 TimeCreated, Id, ProviderName, Message
  $events | ForEach-Object {
    [PSCustomObject]@{
      time = $_.TimeCreated.ToString('o')
      id = $_.Id
      provider = $_.ProviderName
      message = $_.Message
    }
  } | ConvertTo-Json -Depth 4
} catch {
  @{ available = $false; error = $_.Exception.Message } | ConvertTo-Json
}
"""
    try:
        raw = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", ps],
            text=True,
            timeout=60,
            stderr=subprocess.STDOUT,
        )
        data = json.loads(raw) if raw.strip() else []
        payload = {"available": True, "events": data if isinstance(data, list) else [data]}
    except Exception as exc:  # noqa: BLE001
        payload = {"available": False, "reason": str(exc)}
    write_json(out_path, payload)
    return payload


def run_attempt(
    *,
    configuration_id: str,
    attempt_index: int,
    records: list[dict],
) -> dict:
    live_so_far = count_live_loads(records)
    cfg = CONFIGS[configuration_id]
    is_live = bool(cfg.get("live_load")) and not bool(cfg.get("metadata_only"))
    if is_live and live_so_far >= MAX_LIVE_LOAD_ATTEMPTS:
        raise RuntimeError(f"live load attempt ceiling {MAX_LIVE_LOAD_ATTEMPTS} reached")

    attempt_id = f"attempt-{attempt_index:02d}-{configuration_id}"
    attempt_dir = DIAG_ROOT / "attempts" / attempt_id
    if attempt_dir.exists():
        raise RuntimeError(f"attempt directory exists: {attempt_dir}")
    attempt_dir.mkdir(parents=True)

    host_before = _host_readiness(attempt_dir / "host_before.json")
    write_json(attempt_dir / "configuration.json", {"configuration_id": configuration_id, **cfg})

    result_json = attempt_dir / "worker_result.json"
    progress = attempt_dir / "progress.jsonl"
    stdout_path = attempt_dir / "stdout.log"
    stderr_path = attempt_dir / "stderr.log"

    started = datetime.now(UTC).isoformat()
    cmd = [
        str(PYTHON),
        str(WORKER),
        "--config-id",
        configuration_id,
        "--result-json",
        str(result_json),
        "--progress-jsonl",
        str(progress),
    ]
    with (
        stdout_path.open("w", encoding="utf-8") as out_fh,
        stderr_path.open("w", encoding="utf-8") as err_fh,
    ):
        proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            stdout=out_fh,
            stderr=err_fh,
            text=True,
        )
        pid = proc.pid
        # Heartbeat while waiting
        while proc.poll() is None:
            time.sleep(5)
            mem = system_memory()
            with (attempt_dir / "parent_heartbeat.jsonl").open("a", encoding="utf-8") as hb:
                hb.write(
                    json.dumps(
                        {
                            "ts": datetime.now(UTC).isoformat(),
                            "child_pid": pid,
                            "available_ram_bytes": mem.get("available_ram_bytes"),
                        }
                    )
                    + "\n"
                )
        exit_code = proc.returncode

    ended = datetime.now(UTC).isoformat()
    worker: dict = {}
    if result_json.is_file():
        worker = json.loads(result_json.read_text(encoding="utf-8"))

    last_stage = "unknown"
    if progress.is_file():
        lines = [ln for ln in progress.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if lines:
            last_stage = json.loads(lines[-1]).get("stage", "unknown")

    success = exit_code == 0 and bool(worker.get("success"))
    record = attempt_schema(
        attempt_id=attempt_id,
        configuration_id=configuration_id,
        pid=pid,
        started_at=started,
        ended_at=ended,
        exit_code=exit_code,
        load_stage=worker.get("load_stage") or last_stage,
        success=success,
        extra={
            "live_load": is_live,
            "metadata_only": bool(cfg.get("metadata_only")),
            "host_before": {
                "vram_used_mib": (host_before.get("nvidia_smi") or {}).get("memory_used_mib"),
                "vram_free_mib": (host_before.get("nvidia_smi") or {}).get("memory_free_mib"),
                "available_ram_bytes": (host_before.get("memory") or {}).get("available_ram_bytes"),
                "page_file": (host_before.get("memory") or {}).get("page_file_or_swap"),
            },
            "worker_success": worker.get("success"),
            "generation": worker.get("generation"),
            "error": worker.get("error"),
            "attempt_dir": str(attempt_dir.relative_to(ROOT)).replace("\\", "/"),
        },
    )
    write_json(attempt_dir / "attempt.json", record)
    records.append(record)
    write_json(
        DIAG_ROOT / "attempt_manifest.json",
        {"attempts": records, "live_loads": count_live_loads(records)},
    )
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase",
        choices=["matrix", "qualify", "events-only", "host-only"],
        default="matrix",
    )
    parser.add_argument("--qualify-config", default="QUAL")
    parser.add_argument("--device-map-override", default="")
    args = parser.parse_args()

    DIAG_ROOT.mkdir(parents=True, exist_ok=True)
    _host_readiness(DIAG_ROOT / "host" / "host_readiness.json")
    _collect_windows_events(DIAG_ROOT / "windows-crash-events.json")

    if args.phase == "host-only" or args.phase == "events-only":
        print(json.dumps({"ok": True, "phase": args.phase}, indent=2))
        return 0

    records: list[dict] = []
    manifest_path = DIAG_ROOT / "attempt_manifest.json"
    if manifest_path.is_file():
        records = json.loads(manifest_path.read_text(encoding="utf-8")).get("attempts", [])

    if args.phase == "matrix":
        # Order: E (non-live) then A,B,C; D only if all live loads fail and budget remains
        plan = ["E", "A", "B", "C"]
        idx = len(records) + 1
        for cfg_id in plan:
            # skip if already run
            if any(r.get("configuration_id") == cfg_id for r in records):
                continue
            print(f"==> running {cfg_id}", flush=True)
            rec = run_attempt(configuration_id=cfg_id, attempt_index=idx, records=records)
            idx += 1
            print(
                json.dumps(
                    {
                        "configuration_id": cfg_id,
                        "success": rec["success"],
                        "exit": rec["exit_code"],
                        "status": rec["windows_status_code"],
                    },
                    indent=2,
                ),
                flush=True,
            )
            if cfg_id in {"B", "C"} and rec["success"]:
                break
        live_fail = [r for r in records if r.get("live_load") and not r.get("success")]
        live_ok = [r for r in records if r.get("live_load") and r.get("success")]
        if (
            not live_ok
            and count_live_loads(records) < MAX_LIVE_LOAD_ATTEMPTS
            and not any(r.get("configuration_id") == "D" for r in records)
        ):
            print("==> running D (8-bit diagnostic)", flush=True)
            rec = run_attempt(configuration_id="D", attempt_index=idx, records=records)
            print(
                json.dumps(
                    {
                        "configuration_id": "D",
                        "success": rec["success"],
                        "exit": rec["exit_code"],
                    },
                    indent=2,
                ),
                flush=True,
            )

        write_json(
            DIAG_ROOT / "matrix_summary.json",
            {
                "live_loads": count_live_loads(records),
                "max_live_loads": MAX_LIVE_LOAD_ATTEMPTS,
                "successful_live": [
                    r["configuration_id"]
                    for r in records
                    if r.get("live_load") and r.get("success")
                ],
                "failed_live": [r["configuration_id"] for r in live_fail],
            },
        )
        return 0

    if args.phase == "qualify":
        # Three QUAL runs — each is a live load
        successes = 0
        idx = len(records) + 1
        for i in range(3):
            if count_live_loads(records) >= MAX_LIVE_LOAD_ATTEMPTS:
                print("ceiling reached before completing qualification", flush=True)
                break
            print(f"==> QUAL run {i + 1}/3", flush=True)
            # Use distinct configuration marker via attempt id; config QUAL
            rec = run_attempt(configuration_id="QUAL", attempt_index=idx, records=records)
            idx += 1
            if rec["success"]:
                successes += 1
            elif rec.get("access_violation"):
                print(
                    "access violation during qualification; continuing remaining "
                    "scheduled QUAL runs to measure intermittency within ceiling",
                    flush=True,
                )
        # Count only completed QUAL attempts toward classification
        qual_attempts = [r for r in records if r.get("configuration_id") == "QUAL"]
        successes = sum(1 for r in qual_attempts if r.get("success"))
        status = classify_qualification(successes, 3)
        write_json(
            DIAG_ROOT / "qualification_summary.json",
            {
                "status": status,
                "successes": successes,
                "required": 3,
                "configuration_id": "QUAL",
            },
        )
        print(json.dumps({"qualification": status, "successes": successes}, indent=2))
        return 0 if status == "smoke-qualified" else 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
