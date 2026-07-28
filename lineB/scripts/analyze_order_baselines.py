"""Build fixed-order, random-order and oracle-order final-error baselines."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    analysis_root = Path(config["project"]["output_root"]) / "analysis"
    table = pd.read_csv(analysis_root / "directed_coupling.csv")
    table["direction"] = table["action_i"] + "->" + table["action_j"]

    directions = sorted(table["direction"].unique())
    if len(directions) != 2:
        raise ValueError(
            "Order baseline analysis currently requires exactly two directed action orders; "
            f"observed {directions}."
        )

    pivot = table.pivot_table(
        index=["program_id", "clean_id", "application_order", "parameter_set_index"],
        columns="direction",
        values="actual_path_error",
        aggfunc="first",
    ).dropna(subset=directions)
    pivot = pivot.reset_index()

    first_direction, second_direction = directions
    rng = np.random.default_rng(int(config["project"]["seed"]))
    choose_first = rng.integers(0, 2, size=len(pivot)).astype(bool)

    pivot["fixed_first_direction"] = pivot[first_direction]
    pivot["fixed_second_direction"] = pivot[second_direction]
    pivot["random_order_error"] = np.where(
        choose_first,
        pivot[first_direction],
        pivot[second_direction],
    )
    pivot["oracle_order_error"] = pivot[[first_direction, second_direction]].min(axis=1)
    pivot["worst_order_error"] = pivot[[first_direction, second_direction]].max(axis=1)
    pivot["order_gap"] = pivot["worst_order_error"] - pivot["oracle_order_error"]
    pivot["oracle_direction"] = np.where(
        pivot[first_direction] <= pivot[second_direction],
        first_direction,
        second_direction,
    )

    per_program_path = analysis_root / "per_program_order_baselines.csv"
    pivot.to_csv(per_program_path, index=False)

    summary_rows = [
        {
            "baseline": f"Fixed: {first_direction}",
            "n": len(pivot),
            "mean_final_error": pivot[first_direction].mean(),
            "median_final_error": pivot[first_direction].median(),
        },
        {
            "baseline": f"Fixed: {second_direction}",
            "n": len(pivot),
            "mean_final_error": pivot[second_direction].mean(),
            "median_final_error": pivot[second_direction].median(),
        },
        {
            "baseline": "Random order",
            "n": len(pivot),
            "mean_final_error": pivot["random_order_error"].mean(),
            "median_final_error": pivot["random_order_error"].median(),
        },
        {
            "baseline": "Oracle order",
            "n": len(pivot),
            "mean_final_error": pivot["oracle_order_error"].mean(),
            "median_final_error": pivot["oracle_order_error"].median(),
        },
    ]
    summary = pd.DataFrame(summary_rows)
    summary["mean_gap_to_oracle"] = (
        summary["mean_final_error"] - pivot["oracle_order_error"].mean()
    )
    summary_path = analysis_root / "order_baseline_summary.csv"
    summary.to_csv(summary_path, index=False)

    oracle_rate = pivot["oracle_direction"].value_counts(normalize=True).rename("rate")
    oracle_rate.to_csv(analysis_root / "oracle_direction_rate.csv")
    print(f"Wrote order baselines for {len(pivot)} programs.")


if __name__ == "__main__":
    main()
