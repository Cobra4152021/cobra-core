"""Dataset registry for investigation skill benchmarks."""

from __future__ import annotations

from cobra_core.benchmark.dataset import validate_dataset
from cobra_core.benchmark.schemas import BenchmarkDataset


class DatasetRegistry:
    def __init__(self) -> None:
        self._datasets: dict[str, BenchmarkDataset] = {}

    def register(self, dataset: BenchmarkDataset) -> None:
        issues = validate_dataset(dataset)
        if issues:
            raise ValueError("; ".join(issues))
        key = f"{dataset.dataset_id}@{dataset.version}"
        self._datasets[key] = dataset
        # Also index bare id → latest registered version for convenience.
        self._datasets[dataset.dataset_id] = dataset

    def get(self, dataset_id: str, version: str | None = None) -> BenchmarkDataset:
        if version:
            key = f"{dataset_id}@{version}"
            if key not in self._datasets:
                raise KeyError(f"dataset not found: {key}")
            return self._datasets[key]
        if dataset_id not in self._datasets:
            raise KeyError(f"dataset not found: {dataset_id}")
        return self._datasets[dataset_id]

    def list_ids(self) -> list[str]:
        # Unique dataset_id values (no @version keys).
        ids = {d.dataset_id for d in self._datasets.values()}
        return sorted(ids)

    def list_datasets(self) -> list[BenchmarkDataset]:
        seen: set[str] = set()
        out: list[BenchmarkDataset] = []
        for ds in self._datasets.values():
            key = f"{ds.dataset_id}@{ds.version}"
            if key in seen:
                continue
            seen.add(key)
            out.append(ds)
        return sorted(out, key=lambda d: (d.dataset_id, d.version))


DATASET_REGISTRY = DatasetRegistry()
