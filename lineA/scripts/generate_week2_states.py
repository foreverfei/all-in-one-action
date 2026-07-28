"""Generate counterfactual subset-state lattices for all degradation-pair orders."""
from __future__ import annotations

import argparse
import json
from itertools import permutations
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from PIL import Image

from lineA.degradation_program import DegradationProgram, DegradationStep
from lineA.degradations import sample_parameters
from lineA.lattice_renderer import render_program, render_subset


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def make_mock_clean(index: int, size: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed + index)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    xx /= max(size - 1, 1)
    yy /= max(size - 1, 1)
    phase = float(rng.uniform(0.0, 2.0 * np.pi))
    image = np.stack(
        [
            xx,
            yy,
            0.5 + 0.2 * np.sin(4.0 * np.pi * xx + phase) * np.cos(3.0 * np.pi * yy),
        ],
        axis=-1,
    )
    return np.clip(image, 0.0, 1.0).astype(np.float32)


def load_clean_images(input_dir: Path, size: int) -> list[tuple[str, np.ndarray]]:
    records: list[tuple[str, np.ndarray]] = []
    for path in sorted(input_dir.glob("*")):
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp"}:
            continue
        image = Image.open(path).convert("RGB").resize((size, size), Image.Resampling.BICUBIC)
        records.append((path.stem, np.asarray(image, dtype=np.float32) / 255.0))
    if not records:
        raise FileNotFoundError(f"No clean images found in {input_dir}.")
    return records


def save_array(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, np.asarray(array, dtype=np.float32))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--input-dir", type=Path)
    parser.add_argument("--mock-clean-count", type=int, default=0)
    args = parser.parse_args()

    config = load_yaml(args.config)
    project = config["project"]
    size = int(project["image_size"])
    seed = int(project["seed"])

    if args.mock_clean_count > 0:
        clean_records = [
            (f"mock_{index:04d}", make_mock_clean(index, size, seed))
            for index in range(args.mock_clean_count)
        ]
    elif args.input_dir:
        clean_records = load_clean_images(args.input_dir, size)
    else:
        raise ValueError("Provide --input-dir or --mock-clean-count.")

    data_root = Path(project["data_root"])
    master_rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []

    for clean_id, clean in clean_records:
        save_array(data_root / "clean" / f"{clean_id}.npy", clean)
        for pair in config["degradation_pairs"]:
            pair_seed = int(master_rng.integers(0, 2**31 - 1))
            pair_rng = np.random.default_rng(pair_seed)
            sampled = {
                name: sample_parameters(name, config["degradations"][name], pair_rng)
                for name in pair
            }

            for order in permutations(pair, 2):
                steps: list[DegradationStep] = []
                for position, name in enumerate(order):
                    parameters = dict(sampled[name].parameters)
                    steps.append(
                        DegradationStep(
                            name=name,
                            order=position,
                            parameters=parameters,
                            seed=parameters.get("seed"),
                        )
                    )

                program_id = f"{clean_id}__{'-'.join(order)}__seed{pair_seed}"
                program = DegradationProgram(program_id, clean_id, tuple(steps))
                program_dir = data_root / "programs" / program_id

                source_path = program_dir / "source.npy"
                clean_path = program_dir / "clean.npy"
                save_array(source_path, render_program(clean, program))
                save_array(clean_path, clean)

                oracle_mid_paths: dict[str, str] = {}
                for removed_name in pair:
                    remaining = set(pair) - {removed_name}
                    action = program.action_for(removed_name)
                    path = program_dir / f"oracle_mid__{action}.npy"
                    save_array(path, render_subset(clean, program, remaining))
                    oracle_mid_paths[removed_name] = str(path)

                metadata = {
                    **program.to_dict(),
                    "pair_seed": pair_seed,
                    "source_degradations": list(pair),
                    "application_order": list(order),
                    "clean_path": str(clean_path),
                    "source_path": str(source_path),
                    "oracle_mid_paths": oracle_mid_paths,
                }
                metadata_path = program_dir / "metadata.json"
                metadata_path.write_text(
                    json.dumps(metadata, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                rows.append(
                    {
                        "program_id": program_id,
                        "clean_id": clean_id,
                        "program_dir": str(program_dir),
                        "metadata_path": str(metadata_path),
                    }
                )

    data_root.mkdir(parents=True, exist_ok=True)
    with (data_root / "manifest.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Generated {len(rows)} degradation programs at {data_root}.")


if __name__ == "__main__":
    main()
