"""Generate original synthetic KC-002 micro-dataset (Apache-2.0 redistributable)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw


def main() -> None:
    root = Path(__file__).resolve().parents[2] / "data" / "kc002"
    img_dir = root / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    colors = [
        ("red", (220, 40, 40)),
        ("green", (40, 180, 60)),
        ("blue", (40, 80, 220)),
        ("yellow", (230, 210, 40)),
    ]
    shapes = ["square", "circle"]
    items: list[dict] = []
    idx = 0
    for split, n in (("train", 12), ("eval", 4)):
        for i in range(n):
            color_name, rgb = colors[i % len(colors)]
            shape = shapes[i % len(shapes)]
            count = (i % 3) + 1
            im = Image.new("RGB", (384, 384), (245, 245, 245))
            d = ImageDraw.Draw(im)
            for c in range(count):
                x0 = 40 + c * 110
                y0 = 120
                box = [x0, y0, x0 + 90, y0 + 90]
                if shape == "square":
                    d.rectangle(box, fill=rgb, outline=(0, 0, 0), width=3)
                else:
                    d.ellipse(box, fill=rgb, outline=(0, 0, 0), width=3)
            rel = f"images/{split}_{idx:03d}.png"
            path = root / rel
            im.save(path)
            items.append(
                {
                    "id": f"kc002-{split}-{idx:03d}",
                    "split": split,
                    "image_relpath": rel,
                    "image_source": "cobra-original-synthetic",
                    "creator": "Cobra Core KC-002",
                    "license": "Apache-2.0 (original synthetic; redistributable)",
                    "creation_date": "2026-07-23",
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "category": "counting_color_shape",
                    "question": f"How many {color_name} {shape}s are visible?",
                    "expected_answer": str(count),
                    "acceptable_variants": [str(count), f"{count}.", f"There are {count}."],
                }
            )
            idx += 1

            im2 = Image.new("RGB", (384, 384), rgb)
            d2 = ImageDraw.Draw(im2)
            d2.rectangle([96, 96, 288, 288], outline=(0, 0, 0), width=8)
            rel2 = f"images/{split}_color_{idx:03d}.png"
            path2 = root / rel2
            im2.save(path2)
            items.append(
                {
                    "id": f"kc002-{split}-color-{idx:03d}",
                    "split": split,
                    "image_relpath": rel2,
                    "image_source": "cobra-original-synthetic",
                    "creator": "Cobra Core KC-002",
                    "license": "Apache-2.0 (original synthetic; redistributable)",
                    "creation_date": "2026-07-23",
                    "sha256": hashlib.sha256(path2.read_bytes()).hexdigest(),
                    "category": "color",
                    "question": "What is the dominant color of this image?",
                    "expected_answer": color_name,
                    "acceptable_variants": [
                        color_name,
                        color_name.capitalize(),
                        f"the color is {color_name}",
                    ],
                }
            )
            idx += 1

    with (root / "manifest.jsonl").open("w", encoding="utf-8") as f:
        for row in items:
            f.write(json.dumps(row) + "\n")
    print(f"wrote {len(items)} items to {root}")


if __name__ == "__main__":
    main()
