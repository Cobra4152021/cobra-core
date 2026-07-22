"""RuntimeEnvironment schema tests."""

from __future__ import annotations

from datetime import UTC, datetime

from cobra_core.environment.probe import select_inference_strategy
from cobra_core.schemas.runtime import DiskVolume, RuntimeEnvironment


def test_runtime_environment_schema() -> None:
    env = RuntimeEnvironment(
        collected_at=datetime.now(UTC),
        os_name="Windows",
        python_version="3.13.5",
        disk=DiskVolume(path="D:\\", free_bytes=1000, total_bytes=2000, filesystem="exFAT"),
        gpu_count=1,
        unknowns=["example"],
    )
    assert env.disk.filesystem == "exFAT"
    assert env.model_dump()["unknowns"] == ["example"]


def test_strategy_selects_4bit_when_vram_low() -> None:
    strategy = select_inference_strategy(gpu_memory_mib=12282, model_bf16_memory_mib=16000)
    assert strategy["runtime"] == "transformers"
    assert "4bit" in str(strategy["precision"])
