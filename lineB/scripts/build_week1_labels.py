"""Build immediate-gain, directed-influence and identity CSV files."""

from __future__ import annotations

import argparse
import csv
import json
from itertools import permutations
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from lineB.metrics import QualityEvaluator


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def subtract(left: dict[str, float], right: dict[str, float]) -> dict[str, float]:
    if left.keys() != right.keys():
        raise ValueError(f"Metric mismatch: {left.keys()} vs {right.keys()}.")
    return {key: left[key] - right[key] for key in left}


def add(*vectors: dict[str, float]) -> dict[str, float]:
    keys = vectors[0].keys()
    if any(vector.keys() != keys for vector in vectors):
        raise ValueError("Metric keys differ between vectors.")
    return {key: sum(vector[key] for vector in vectors) for key in keys}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No rows generated for {path}.")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--metrics",
        default="psnr,lpips,dists",
        help="Comma-separated subset of psnr,lpips,dists.",
    )
    args = parser.parse_args()

    config = load_yaml(args.config)
    actions = tuple(config["actions"])
    data_root = Path(config["project"]["data_root"])
    output_root = Path(config["project"]["output_root"])
    rollout_root = output_root / "rollouts"
    label_root = output_root / "labels"
    manifest = load_jsonl(data_root / "manifest.jsonl")
    evaluator = QualityEvaluator(args.metrics.split(","))

    gain_rows: list[dict[str, Any]] = []
    influence_rows: list[dict[str, Any]] = []
    identity_rows: list[dict[str, Any]] = []

    for record in manifest:
        sample_id = record["sample_id"]
        sample_dir = rollout_root / sample_id
        ground_truth = np.load(record["clean_path"]).astype(np.float32)
        state = np.load(sample_dir / "input.npy").astype(np.float32)

        quality_state = evaluator.quality_vector(state, ground_truth)
        qualities_single: dict[str, dict[str, float]] = {}
        gains: dict[str, dict[str, float]] = {}

        for action in actions:
            output = np.load(sample_dir / f"{action}.npy").astype(np.float32)
            quality = evaluator.quality_vector(output, ground_truth)
            qualities_single[action] = quality
            gains[action] = subtract(quality, quality_state)
            gain_rows.append({"sample_id": sample_id, "action": action, **gains[action]})

        for first, second in permutations(actions, 2):
            pair = np.load(sample_dir / f"{first}__{second}.npy").astype(np.float32)
            quality_pair = evaluator.quality_vector(pair, ground_truth)

            influence = add(
                quality_pair,
                {key: -value for key, value in qualities_single[first].items()},
                {key: -value for key, value in qualities_single[second].items()},
                quality_state,
            )
            influence_rows.append(
                {
                    "sample_id": sample_id,
                    "action_a": first,
                    "action_b": second,
                    **{f"eta_{key}": value for key, value in influence.items()},
                }
            )

            lhs = subtract(quality_pair, quality_state)
            rhs = add(gains[first], gains[second], influence)
            errors = {key: abs(lhs[key] - rhs[key]) for key in lhs}
            identity_rows.append(
                {
                    "sample_id": sample_id,
                    "action_a": first,
                    "action_b": second,
                    **{f"error_{key}": value for key, value in errors.items()},
                    "max_error": max(errors.values()),
                }
            )

    write_csv(label_root / "gain_labels.csv", gain_rows)
    write_csv(label_root / "influence_labels.csv", influence_rows)
    write_csv(label_root / "identity_check.csv", identity_rows)
    print(f"Labels written to {label_root}.")


if __name__ == "__main__":
    main()
