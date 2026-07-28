"""Analyze coupling variation against predecessor error, severity and order."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    analysis_root = Path(config["project"]["output_root"]) / "analysis"
    table = pd.read_csv(analysis_root / "directed_coupling.csv")

    state_rows: list[dict] = []
    for (action_i, action_j), group in table.groupby(["action_i", "action_j"]):
        state_rows.append(
            {
                "action_i": action_i,
                "action_j": action_j,
                "n": len(group),
                "signed_mean": group["signed_coupling"].mean(),
                "signed_std": group["signed_coupling"].std(),
                "spearman_mid_error": group["mid_error"].rank().corr(
                    group["signed_coupling"].rank()
                ),
                "spearman_severity": group["severity_score"].rank().corr(
                    group["signed_coupling"].rank()
                ),
                "direction_reversal_rate": min(
                    (group["signed_coupling"] > 0).mean(),
                    (group["signed_coupling"] < 0).mean(),
                ),
            }
        )

    pd.DataFrame(state_rows).to_csv(
        analysis_root / "state_dependence_report.csv",
        index=False,
    )

    matched_rows: list[dict] = []
    for (action_i, action_j), group in table.groupby(["action_i", "action_j"]):
        group = group.copy()
        try:
            group["mid_error_bin"] = pd.qcut(
                group["mid_error"],
                3,
                labels=["low", "medium", "high"],
                duplicates="drop",
            )
        except ValueError:
            group["mid_error_bin"] = "all"

        for bin_name, subset in group.groupby("mid_error_bin", observed=True):
            matched_rows.append(
                {
                    "action_i": action_i,
                    "action_j": action_j,
                    "mid_error_bin": str(bin_name),
                    "n": len(subset),
                    "mid_error_mean": subset["mid_error"].mean(),
                    "coupling_mean": subset["signed_coupling"].mean(),
                    "coupling_std": subset["signed_coupling"].std(),
                }
            )

    pd.DataFrame(matched_rows).to_csv(
        analysis_root / "matched_error_analysis.csv",
        index=False,
    )
    print("Wrote state-dependence and matched-error reports.")


if __name__ == "__main__":
    main()
