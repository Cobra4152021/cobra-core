"""
KC-030 — Investigation Evaluation & Benchmark Framework.

Measures Investigation Skill quality. Does not change routing, providers,
or production approval queues.
"""

from cobra_core.benchmark.config import BenchmarkConfig, load_benchmark_config
from cobra_core.benchmark.engine import BenchmarkEngine
from cobra_core.benchmark.registry import DATASET_REGISTRY, DatasetRegistry

# Register built-in investigation datasets (versioned gold standards).
from cobra_core.benchmark.datasets import register_builtin_datasets  # noqa: E402,F401

__all__ = [
    "BenchmarkConfig",
    "BenchmarkEngine",
    "DATASET_REGISTRY",
    "DatasetRegistry",
    "load_benchmark_config",
]
