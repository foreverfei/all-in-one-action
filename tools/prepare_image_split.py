"""Prepare a deterministic image subset without modifying source files."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--mode", choices=["copy", "symlink"], default="symlink")
    args = parser.parse_args()

    if args.count <= 0 or args.offset < 0:
        raise ValueError("count must be positive and offset must be non-negative")

    images = [
        path
        for path in sorted(args.input_dir.iterdir())
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    ]
    selected = images[args.offset : args.offset + args.count]
    if len(selected) != args.count:
        raise ValueError(
            f"Requested {args.count} images from offset {args.offset}, "
            f"but only {len(selected)} are available."
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    existing = [path for path in args.output_dir.iterdir() if path.is_file() or path.is_symlink()]
    if existing:
        raise FileExistsError(
            f"Output directory is not empty: {args.output_dir}. "
            "Use a new directory or remove the old split explicitly."
        )

    for source in selected:
        target = args.output_dir / source.name
        if args.mode == "copy":
            shutil.copy2(source, target)
        else:
            target.symlink_to(source.resolve())

    manifest = args.output_dir / "SPLIT.txt"
    manifest.write_text(
        "\n".join(path.name for path in selected) + "\n",
        encoding="utf-8",
    )
    print(
        f"Prepared {len(selected)} images at {args.output_dir} "
        f"using mode={args.mode}."
    )


if __name__ == "__main__":
    main()
