"""Load KC-002 legally cleared micro-dataset."""

from __future__ import annotations

import json
from pathlib import Path


def load_micro_dataset(root: Path) -> list[dict]:
    manifest = root / "manifest.jsonl"
    if not manifest.exists():
        raise FileNotFoundError(f"missing {manifest}")
    rows = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        img = root / row["image_relpath"]
        row["image_path"] = str(img)
        if not img.exists():
            raise FileNotFoundError(f"missing image {img}")
        rows.append(row)
    return rows
