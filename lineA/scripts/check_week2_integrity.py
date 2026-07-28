"""Validate Week-2 subset states and rollout files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import yaml

from lineA.degradation_program import DegradationProgram
from lineA.lattice_renderer import render_program, render_subset


def check_array(path: Path, expected_shape: tuple[int, ...]) -> np.ndarray:
    array = np.load(path)
    if array.shape != expected_shape:
        raise AssertionError(f"{path}: shape {array.shape} != {expected_shape}")
    if array.dtype != np.float32:
        raise AssertionError(f"{path}: dtype {array.dtype} is not float32")
    if not np.isfinite(array).all():
        raise AssertionError(f"{path}: contains NaN or Inf")
    if float(array.min()) < -1e-6 or float(array.max()) > 1.0 + 1e-6:
        raise AssertionError(f"{path}: values are outside [0,1]")
    return array


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    output_root = Path(config["project"]["output_root"])
    rollout_root = output_root / "rollouts"
    failures: list[dict[str, str]] = []
    valid_programs = 0

    for program_dir in sorted(rollout_root.glob("*")):
        try:
            metadata = json.loads(
                (program_dir / "metadata.json").read_text(encoding="utf-8")
            )
            program = DegradationProgram.from_dict(metadata)
            clean = np.load(program_dir / "clean.npy").astype(np.float32)
            shape = clean.shape
            source = check_array(program_dir / "source.npy", shape)

            expected_source = render_program(clean, program)
            if not np.allclose(source, expected_source, atol=1e-7):
                raise AssertionError("source does not match the recorded degradation program")

            for direction in metadata["directions"]:
                action_i = direction["action_i"]
                action_j = direction["action_j"]
                remaining = direction["remaining_degradation"]

                oracle_mid = check_array(
                    program_dir / f"oracle_mid__{action_i}.npy",
                    shape,
                )
                expected_oracle = render_subset(clean, program, {remaining})
                if not np.allclose(oracle_mid, expected_oracle, atol=1e-7):
                    raise AssertionError(f"oracle subset mismatch for {action_i}")

                required = [
                    f"actual_mid__{action_i}.npy",
                    f"actual_final__{action_i}__{action_j}.npy",
                    f"oracle_successor__{action_i}__{action_j}.npy",
                ]
                for filename in required:
                    check_array(program_dir / filename, shape)

            valid_programs += 1
        except Exception as exc:
            failures.append({"program_dir": str(program_dir), "error": str(exc)})

    report = {
        "program_count": valid_programs,
        "failure_count": len(failures),
        "failures": failures,
    }
    report_path = output_root / "week2_integrity_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if failures:
        raise SystemExit(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
