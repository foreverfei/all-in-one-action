"""Generate actual and oracle-successor rollouts for each directed path."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from lineA.degradation_program import DegradationProgram
from lineA.executors.base import MockExecutor, RestorationExecutor


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def build_executor(config: dict[str, Any], name: str) -> RestorationExecutor:
    if name == "mock":
        return MockExecutor()
    if name == "instructir":
        from lineA.executors.instructir_wrapper import InstructIRExecutor

        prompts_path = Path(
            config.get("baseline", {}).get("prompts_file", "shared/action_prompts.yaml")
        )
        prompts = yaml.safe_load(prompts_path.read_text(encoding="utf-8"))
        executor_cfg = config["executor"]
        return InstructIRExecutor.from_external(
            external_repo=executor_cfg["external_repo"],
            config_file=executor_cfg["config_path"],
            image_checkpoint=executor_cfg["image_checkpoint"],
            lm_head_checkpoint=executor_cfg["lm_head_checkpoint"],
            prompts=prompts,
            device=executor_cfg.get("device", "cuda"),
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
    data_root = Path(config["project"]["data_root"])
    output_root = Path(config["project"]["output_root"]) / "rollouts"
    executor = build_executor(config, args.executor)

    for row in load_jsonl(data_root / "manifest.jsonl"):
        metadata = json.loads(Path(row["metadata_path"]).read_text(encoding="utf-8"))
        program = DegradationProgram.from_dict(metadata)
        source = np.load(metadata["source_path"]).astype(np.float32)
        clean = np.load(metadata["clean_path"]).astype(np.float32)
        program_dir = output_root / program.program_id

        save_array(program_dir / "source.npy", source)
        save_array(program_dir / "clean.npy", clean)

        degradation_names = [step.name for step in program.ordered_steps()]
        directions: list[dict[str, str]] = []

        for removed_name in degradation_names:
            remaining_name = next(name for name in degradation_names if name != removed_name)
            action_i = program.action_for(removed_name)
            action_j = program.action_for(remaining_name)
            oracle_mid = np.load(metadata["oracle_mid_paths"][removed_name]).astype(np.float32)

            actual_mid = executor.restore(source, action_i)
            actual_final = executor.restore(actual_mid, action_j)
            oracle_successor = executor.restore(oracle_mid, action_j)

            save_array(program_dir / f"oracle_mid__{action_i}.npy", oracle_mid)
            save_array(program_dir / f"actual_mid__{action_i}.npy", actual_mid)
            save_array(
                program_dir / f"actual_final__{action_i}__{action_j}.npy",
                actual_final,
            )
            save_array(
                program_dir / f"oracle_successor__{action_i}__{action_j}.npy",
                oracle_successor,
            )
            directions.append(
                {
                    "action_i": action_i,
                    "action_j": action_j,
                    "removed_degradation": removed_name,
                    "remaining_degradation": remaining_name,
                }
            )

        output_metadata = {
            **metadata,
            "experiment": config.get("experiment", {}),
            "baseline": config.get("baseline", {}),
            "executor": args.executor,
            "executor_checkpoint": getattr(executor, "checkpoint", "mock-executor"),
            "directions": directions,
        }
        (program_dir / "metadata.json").write_text(
            json.dumps(output_metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(f"Generated Week-2 rollouts at {output_root}.")


if __name__ == "__main__":
    main()
