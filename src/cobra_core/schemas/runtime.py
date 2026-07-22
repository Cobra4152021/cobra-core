"""Runtime / hardware environment inventory schema."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field


class GpuDevice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    index: int
    name: str
    total_memory_bytes: int | None = None
    total_memory_mib: float | None = None
    driver_model: str | None = None


class DiskVolume(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    total_bytes: int | None = None
    free_bytes: int | None = None
    filesystem: str | None = None
    supports_large_files: bool | None = None
    supports_large_files_note: str | None = None


class RuntimeEnvironment(BaseModel):
    """Local machine inventory for acquisition and inference decisions."""

    model_config = ConfigDict(extra="allow")

    collected_at: datetime
    os_name: str
    os_version: str | None = None
    python_version: str
    python_executable: str | None = None
    disk: DiskVolume
    ram_total_bytes: int | None = None
    ram_available_bytes: int | None = None
    gpu_count: int = 0
    gpus: list[GpuDevice] = Field(default_factory=list)
    cuda_available: bool | None = None
    cuda_version: str | None = None
    nvidia_driver_version: str | None = None
    torch_version: str | None = None
    transformers_version: str | None = None
    flash_attention_available: bool | None = None
    bitsandbytes_available: bool | None = None
    accelerate_available: bool | None = None
    huggingface_hub_version: str | None = None
    cobra_model_home: str | None = None
    selected_inference_runtime: str | None = None
    selected_precision: str | None = None
    selection_rationale: str | None = None
    unknowns: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class StorageGateResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_model_bytes: Annotated[int, Field(ge=0)]
    temporary_overhead_bytes: Annotated[int, Field(ge=0)]
    safety_margin_bytes: Annotated[int, Field(ge=0)]
    required_free_bytes: Annotated[int, Field(ge=0)]
    available_free_bytes: Annotated[int, Field(ge=0)]
    passed: bool
    message: str
