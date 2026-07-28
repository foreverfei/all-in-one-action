"""Analyze coupling variation against predecessor error, severity and order."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import yaml


def spearman(group: pd.DataFrame, column: str) -> float:
    if column not in group or group[column].nunique(dropna=True) < 2:
        return float("nan")
    return float(group[column].rank().corr(group["signed_coupling"].rank()))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    analysis_root = Path(config["project"]["output_root"]) / "analysis"
    table = pd.read_csv(analysis_root / "directed_coupling.csv")
    bin_count = int(config.get("reporting", {}).get("matched_error_bins", 3))

    state_rows: list[dict] = []
    for (action_i, action_j), group in table.groupby(["action_i", "action_j"]):
        state_rows.append(
            {
                "action_i": action_i,
                "action_j": action_j,
                "n": len(group),
                "signed_mean": group["signed_coupling"].mean(),
                "signed_std": group["signed_coupling"].std(),
                "spearman_mid_error": spearman(group, "mid_error"),
                "spearman_severity": spearman(group, "severity_score"),
                "spearman_noise_sigma": spearman(group, "noise_sigma"),
                "spearman_blur_length": spearman(group, "blur_length"),
                "spearman_blur_angle": spearman(group, "blur_angle_deg"),
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

    parameter_rows: list[dict] = []
    parameter_columns = [
        column
        for column in ("noise_sigma", "blur_length", "blur_angle_deg", "application_order")
        if column in table.columns
    ]
    for (action_i, action_j), group in table.groupby(["action_i", "action_j"]):
        for parameter in parameter_columns:
            for value, subset in group.groupby(parameter, dropna=False):
                parameter_rows.append(
                    {
                        "action_i": action_i,
                        "action_j": action_j,
                        "parameter": parameter,
                        "value": value,
                        "n": len(subset),
                        "mid_error_mean": subset["mid_error"].mean(),
                        "coupling_mean": subset["signed_coupling"].mean(),
                        "coupling_std": subset["signed_coupling"].std(),
                        "positive_rate": (subset["signed_coupling"] > 0).mean(),
                    }
                )
    pd.DataFrame(parameter_rows).to_csv(
        analysis_root / "parameter_conditioned_summary.csv",
        index=False,
    )

    matched_rows: list[dict] = []
    for (action_i, action_j), group in table.groupby(["action_i", "action_j"]):
        group = group.copy()
        try:
            labels = [f"q{index + 1}" for index in range(bin_count)]
            group["mid_error_bin"] = pd.qcut(
                group["mid_error"],
                bin_count,
                labels=labels,
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
                    "positive_rate": (subset["signed_coupling"] > 0).mean(),
                }
            )

    pd.DataFrame(matched_rows).to_csv(
        analysis_root / "matched_error_analysis.csv",
        index=False,
    )
    print("Wrote state, parameter-conditioned and matched-error reports.")


if __name__ == "__main__":
    main()
