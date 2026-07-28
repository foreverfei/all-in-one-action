"""Fail before an experiment if configured data/output roots are non-empty."""
from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def is_nonempty(path: Path) -> bool:
    return path.exists() and any(path.iterdir())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    paths = [
        Path(config["project"]["data_root"]),
        Path(config["project"]["output_root"]),
    ]
    occupied = [str(path) for path in paths if is_nonempty(path)]
    if occupied:
        raise SystemExit(
            "Experiment paths are not empty. Use a new experiment config or explicitly "
            f"archive/remove the old outputs first: {occupied}"
        )
    print("PASS: configured data_root and output_root are empty.")


if __name__ == "__main__":
    main()
