"""Generate deterministic Week-1 controlled states."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from PIL import Image

from lineA.degradations import apply_combination, sample_parameters


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def save_image(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.round(np.clip(image, 0, 1) * 255).astype(np.uint8), mode="RGB").save(path)


def make_mock_clean(index: int, size: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed + index)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    xx /= max(size - 1, 1)
    yy /= max(size - 1, 1)
    phase = float(rng.uniform(0, 2 * np.pi))
    image = np.stack(
        [
            xx,
            yy,
            0.5 + 0.25 * np.sin(6 * np.pi * xx + phase) * np.cos(4 * np.pi * yy),
        ],
        axis=-1,
    )
    return np.clip(image, 0.0, 1.0).astype(np.float32)


def load_clean_images(input_dir: Path, size: int) -> list[tuple[str, np.ndarray]]:
    records: list[tuple[str, np.ndarray]] = []
    for path in sorted(input_dir.glob("*")):
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp"}:
            continue
        image = Image.open(path).convert("RGB").resize((size, size), Image.Resampling.BICUBIC)
        records.append((path.stem, np.asarray(image, dtype=np.float32) / 255.0))
    if not records:
        raise FileNotFoundError(f"No images found in {input_dir}.")
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--input-dir", type=Path)
    parser.add_argument("--mock-clean-count", type=int, default=0)
    args = parser.parse_args()

    config = load_yaml(args.config)
    project = config["project"]
    size = int(project["image_size"])
    seed = int(project["seed"])
    data_root = Path(project["data_root"])
    clean_dir = data_root / "clean"
    degraded_dir = data_root / "degraded"
    cfg_dir = data_root / "degradation_configs"
    manifest_path = data_root / "manifest.jsonl"

    if args.mock_clean_count > 0:
        clean_records = [
            (f"mock_{index:04d}", make_mock_clean(index, size, seed))
            for index in range(args.mock_clean_count)
        ]
    elif args.input_dir:
        clean_records = load_clean_images(args.input_dir, size)
    else:
        raise ValueError("Provide --input-dir or --mock-clean-count.")

    combinations = config["degradation_combinations"]
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []

    for index, (clean_id, clean) in enumerate(clean_records):
        combination = list(combinations[index % len(combinations)])
        sample_seed = int(rng.integers(0, 2**31 - 1))
        sample_rng = np.random.default_rng(sample_seed)
        sampled = [
            sample_parameters(name, config["degradations"][name], sample_rng)
            for name in combination
        ]
        degraded = apply_combination(clean, sampled)
        sample_id = f"{clean_id}_{'-'.join(combination)}_seed{sample_seed}"

        clean_npy = clean_dir / f"{sample_id}.npy"
        degraded_npy = degraded_dir / f"{sample_id}.npy"
        clean_preview = clean_dir / f"{sample_id}.png"
        degraded_preview = degraded_dir / f"{sample_id}.png"
        degradation_cfg = cfg_dir / f"{sample_id}.json"

        clean_npy.parent.mkdir(parents=True, exist_ok=True)
        degraded_npy.parent.mkdir(parents=True, exist_ok=True)
        cfg_dir.mkdir(parents=True, exist_ok=True)
        np.save(clean_npy, clean.astype(np.float32))
        np.save(degraded_npy, degraded.astype(np.float32))
        save_image(clean_preview, clean)
        save_image(degraded_preview, degraded)

        sampled_json = [
            {"name": item.name, "parameters": item.parameters}
            for item in sampled
        ]
        degradation_cfg.write_text(
            json.dumps(
                {
                    "sample_id": sample_id,
                    "seed": sample_seed,
                    "degradations": sampled_json,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        rows.append(
            {
                "sample_id": sample_id,
                "seed": sample_seed,
                "clean_path": str(clean_npy),
                "input_path": str(degraded_npy),
                "degradation_config": str(degradation_cfg),
                "degradations": combination,
            }
        )

    data_root.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Generated {len(rows)} samples.")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
