"""Generate all single-step and ordered two-step rollouts."""

from __future__ import annotations

import argparse
import json
import subprocess
from itertools import permutations
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from lineA.executors import InstructIRExecutor, MockExecutor, RestorationExecutor


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def build_executor(config: dict[str, Any], name: str) -> RestorationExecutor:
    if name == "mock":
        return MockExecutor()
    if name == "instructir":
        prompts = load_yaml(Path("shared/action_prompts.yaml"))
        executor_cfg = config["executor"]
        return InstructIRExecutor.from_external(
            external_repo=executor_cfg["external_repo"],
            checkpoint=executor_cfg["checkpoint"],
            prompts=prompts,
        )
    raise ValueError(f"Unknown executor {name!r}.")


def save_array(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, np.asarray(array, dtype=np.float32))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--executor", choices=["mock", "instructir"], default="mock")
    args = parser.parse_args()

    config = load_yaml(args.config)
    actions = tuple(config["actions"])
    data_root = Path(config["project"]["data_root"])
    output_root = Path(config["project"]["output_root"]) / "rollouts"
    manifest = load_jsonl(data_root / "manifest.jsonl")
    executor = build_executor(config, args.executor)

    for row in manifest:
        sample_id = row["sample_id"]
        sample_dir = output_root / sample_id
        sample_dir.mkdir(parents=True, exist_ok=True)
        image = np.load(row["input_path"]).astype(np.float32)
        save_array(sample_dir / "input.npy", image)

        single_outputs: dict[str, np.ndarray] = {}
        for action in actions:
            output = executor.restore(image, action)
            single_outputs[action] = output
            save_array(sample_dir / f"{action}.npy", output)

        for first, second in permutations(actions, 2):
            output = executor.restore(single_outputs[first], second)
            save_array(sample_dir / f"{first}__{second}.npy", output)

        metadata = {
            **row,
            "actions": list(actions),
            "executor": args.executor,
            "checkpoint": str(config["executor"]["checkpoint"]),
            "git_commit": git_commit(),
            "tensor_shape": list(image.shape),
            "tensor_dtype": str(image.dtype),
            "tensor_range": [float(image.min()), float(image.max())],
        }
        (sample_dir / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(f"Generated rollouts for {len(manifest)} samples at {output_root}.")


if __name__ == "__main__":
    main()
