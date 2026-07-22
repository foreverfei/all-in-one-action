"""Fail fast when the exact two-step identity is violated."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=1e-5)
    args = parser.parse_args()

    frame = pd.read_csv(args.labels)
    if frame.empty:
        raise SystemExit("Identity table is empty.")
    if "max_error" not in frame:
        raise SystemExit("Missing max_error column.")

    maximum = float(frame["max_error"].max())
    failures = frame[frame["max_error"] >= args.threshold]
    print(f"rows={len(frame)}, max_error={maximum:.3e}, threshold={args.threshold:.3e}")

    if not failures.empty:
        print(failures.head(20).to_string(index=False))
        raise SystemExit(f"FAIL: {len(failures)} identity row(s) exceed threshold.")

    print("PASS: exact two-step identity is satisfied.")


if __name__ == "__main__":
    main()
