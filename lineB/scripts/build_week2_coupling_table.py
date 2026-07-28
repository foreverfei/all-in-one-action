"""Build one row per directed action path."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from lineB.coupling.directed_coupling import compute_directed_coupling
from lineB.coupling.error_metrics import severity_score


def degradation_fields(metadata: dict) -> dict[str, float]:
    fields: dict[str, float] = {}
    for step in metadata.get("degradation_program", []):
        name = str(step["type"])
        parameters = step.get("parameters", {})
        if name == "noise":
            fields["noise_sigma"] = float(parameters["sigma"])
        elif name == "motion_blur":
            fields["blur_length"] = float(parameters["length"])
            fields["blur_angle_deg"] = float(parameters["angle_deg"])
        elif name == "haze":
            fields["haze_transmission"] = float(parameters["transmission"])
            fields["haze_atmospheric_light"] = float(parameters["atmospheric_light"])
        elif name == "rain":
            fields["rain_density"] = float(parameters["density"])
            fields["rain_length"] = float(parameters["length"])
            fields["rain_opacity"] = float(parameters["opacity"])
        elif name == "lowlight":
            fields["lowlight_gamma"] = float(parameters["gamma"])
            fields["lowlight_scale"] = float(parameters["scale"])
    return fields


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    rollout_root = Path(config["project"]["output_root"]) / "rollouts"
    epsilon = float(config["coupling"]["charbonnier_epsilon"])
    rows: list[dict] = []

    for program_dir in sorted(rollout_root.glob("*")):
        metadata = json.loads(
            (program_dir / "metadata.json").read_text(encoding="utf-8")
        )
        clean = np.load(program_dir / "clean.npy")
        directions = metadata["directions"]
        final_outputs = {
            (direction["action_i"], direction["action_j"]): np.load(
                program_dir
                / f"actual_final__{direction['action_i']}__{direction['action_j']}.npy"
            )
            for direction in directions
        }
        raw_parameters = degradation_fields(metadata)

        for direction in directions:
            action_i = direction["action_i"]
            action_j = direction["action_j"]
            result = compute_directed_coupling(
                actual_mid=np.load(program_dir / f"actual_mid__{action_i}.npy"),
                oracle_mid=np.load(program_dir / f"oracle_mid__{action_i}.npy"),
                oracle_successor=np.load(
                    program_dir / f"oracle_successor__{action_i}__{action_j}.npy"
                ),
                actual_final=final_outputs[(action_i, action_j)],
                final_target=clean,
                reverse_actual_final=final_outputs[(action_j, action_i)],
                epsilon=epsilon,
            )
            rows.append(
                {
                    "experiment_id": metadata.get("experiment", {}).get("id", "unspecified"),
                    "executor": metadata.get("executor", "unknown"),
                    "executor_checkpoint": metadata.get("executor_checkpoint", "unknown"),
                    "program_id": metadata["program_id"],
                    "clean_id": metadata["clean_id"],
                    "parameter_set_index": metadata.get("parameter_set_index", -1),
                    "action_i": action_i,
                    "action_j": action_j,
                    "application_order": "->".join(metadata["application_order"]),
                    "severity_score": severity_score(metadata),
                    **raw_parameters,
                    **result.__dict__,
                }
            )

    analysis_root = Path(config["project"]["output_root"]) / "analysis"
    analysis_root.mkdir(parents=True, exist_ok=True)
    output_path = analysis_root / "directed_coupling.csv"
    pd.DataFrame(rows).to_csv(output_path, index=False)
    print(f"Wrote {len(rows)} directed rows to {output_path}.")


if __name__ == "__main__":
    main()
