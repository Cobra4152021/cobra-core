from pathlib import Path

from cobra_kc002.dataset import load_micro_dataset


def test_micro_dataset_loads_and_is_synthetic():
    root = Path(__file__).resolve().parents[2] / "data" / "kc002"
    rows = load_micro_dataset(root)
    assert len(rows) >= 16
    assert all(r["license"].startswith("Apache-2.0") for r in rows)
    assert all(r["image_source"] == "cobra-original-synthetic" for r in rows)
    assert any(r["split"] == "train" for r in rows)
    assert any(r["split"] == "eval" for r in rows)
