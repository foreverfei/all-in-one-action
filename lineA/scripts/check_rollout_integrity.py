"""Validate Week-1 rollout completeness and tensor invariants."""

from __future__ import annotations

import argparse
import json
from itertools import permutations
from pathlib import Path
from typing import Any

import numpy as np
import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def validate_array(path: Path, expected_size: int) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"missing: {path}"]
    array = np.load(path)
    if array.shape != (expected_size, expected_size, 3):
        errors.append(f"{path}: shape={array.shape}")
    if array.dtype != np.float32:
        errors.append(f"{path}: dtype={array.dtype}")
    if not np.isfinite(array).all():
        errors.append(f"{path}: contains NaN/Inf")
    if float(array.min()) < -1e-6 or float(array.max()) > 1.0 + 1e-6:
        errors.append(f"{path}: range=[{array.min()}, {array.max()}]")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    config = load_yaml(args.config)
    actions = tuple(config["actions"])
    size = int(config["project"]["image_size"])
    data_root = Path(config["project"]["data_root"])
    rollout_root = Path(config["project"]["output_root"]) / "rollouts"
    manifest = load_jsonl(data_root / "manifest.jsonl")

    errors: list[str] = []
    for row in manifest:
        sample_dir = rollout_root / row["sample_id"]
        expected = ["input.npy", "metadata.json"]
        expected += [f"{action}.npy" for action in actions]
        expected += [f"{a}__{b}.npy" for a, b in permutations(actions, 2)]
        for filename in expected:
            path = sample_dir / filename
            if filename.endswith(".npy"):
                errors.extend(validate_array(path, size))
            elif not path.exists():
                errors.append(f"missing: {path}")

    if errors:
        print("\n".join(errors))
        raise SystemExit(f"Integrity check failed with {len(errors)} error(s).")

    print(
        f"PASS: {len(manifest)} samples, "
        f"{len(actions)} single actions and {len(actions) * (len(actions)-1)} ordered pairs."
    )


if __name__ == "__main__":
    main()
