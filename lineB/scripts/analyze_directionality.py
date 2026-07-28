"""Summarize directed coupling and paired directional asymmetry."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


def bootstrap_ci(values, sample_count: int, seed: int) -> tuple[float, float]:
    values = np.asarray(values, dtype=np.float64)
    if len(values) == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    means = [
        float(rng.choice(values, size=len(values), replace=True).mean())
        for _ in range(sample_count)
    ]
    low, high = np.quantile(means, [0.025, 0.975])
    return float(low), float(high)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    analysis_root = Path(config["project"]["output_root"]) / "analysis"
    table = pd.read_csv(analysis_root / "directed_coupling.csv")
    bootstrap_samples = int(config["coupling"]["bootstrap_samples"])
    bootstrap_seed = int(config["coupling"]["bootstrap_seed"])

    rows: list[dict] = []
    for (action_i, action_j), group in table.groupby(["action_i", "action_j"]):
        ci_low, ci_high = bootstrap_ci(
            group["signed_coupling"],
            bootstrap_samples,
            bootstrap_seed,
        )
        rows.append(
            {
                "action_i": action_i,
                "action_j": action_j,
                "n": len(group),
                "mean_signed_coupling": group["signed_coupling"].mean(),
                "mean_harmful_coupling": group["harmful_coupling"].mean(),
                "mean_non_commutativity": group["non_commutativity"].mean(),
                "positive_rate": (group["signed_coupling"] > 0).mean(),
                "negative_rate": (group["signed_coupling"] < 0).mean(),
                "ci95_low": ci_low,
                "ci95_high": ci_high,
            }
        )

    summary_path = analysis_root / "directionality_summary.csv"
    pd.DataFrame(rows).to_csv(summary_path, index=False)

    paired = table.copy()
    paired["direction"] = paired["action_i"] + "->" + paired["action_j"]
    paired["action_pair"] = paired.apply(
        lambda row: "|".join(sorted([str(row["action_i"]), str(row["action_j"])])),
        axis=1,
    )
    asymmetry_rows: list[dict] = []
    for action_pair, group in paired.groupby("action_pair"):
        directions = sorted(group["direction"].unique())
        if len(directions) != 2:
            continue
        pivot = group.pivot_table(
            index="program_id",
            columns="direction",
            values="signed_coupling",
            aggfunc="first",
        ).dropna(subset=directions)
        difference = pivot[directions[0]] - pivot[directions[1]]
        ci_low, ci_high = bootstrap_ci(
            difference,
            bootstrap_samples,
            bootstrap_seed + 1,
        )
        asymmetry_rows.append(
            {
                "action_pair": action_pair,
                "direction_positive": directions[0],
                "direction_negative": directions[1],
                "n_paired_programs": len(difference),
                "mean_directional_difference": difference.mean(),
                "median_directional_difference": difference.median(),
                "positive_difference_rate": (difference > 0).mean(),
                "ci95_low": ci_low,
                "ci95_high": ci_high,
            }
        )

    asymmetry_path = analysis_root / "directional_asymmetry.csv"
    pd.DataFrame(asymmetry_rows).to_csv(asymmetry_path, index=False)
    print(
        f"Wrote {len(rows)} direction summaries and "
        f"{len(asymmetry_rows)} paired asymmetry rows."
    )


if __name__ == "__main__":
    main()
