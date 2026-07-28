"""Generate counterfactual subset-state lattices for degradation-pair orders."""
from __future__ import annotations

import argparse
import json
from itertools import permutations, product
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from PIL import Image

from lineA.degradation_program import DegradationProgram, DegradationStep
from lineA.degradations import SampledDegradation, sample_parameters
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


def prepare_image(path: Path, size: int, mode: str) -> np.ndarray:
    image = Image.open(path).convert("RGB")
    if mode == "resize":
        image = image.resize((size, size), Image.Resampling.BICUBIC)
    elif mode == "center_crop":
        width, height = image.size
        if min(width, height) < size:
            scale = size / min(width, height)
            image = image.resize(
                (int(round(width * scale)), int(round(height * scale))),
                Image.Resampling.BICUBIC,
            )
            width, height = image.size
        left = (width - size) // 2
        top = (height - size) // 2
        image = image.crop((left, top, left + size, top + size))
    else:
        raise ValueError(f"Unknown image_preprocess mode: {mode!r}")
    return np.asarray(image, dtype=np.float32) / 255.0


def load_clean_images(input_dir: Path, size: int, mode: str) -> list[tuple[str, np.ndarray]]:
    records: list[tuple[str, np.ndarray]] = []
    for path in sorted(input_dir.glob("*")):
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp"}:
            continue
        records.append((path.stem, prepare_image(path, size, mode)))
    if not records:
        raise FileNotFoundError(f"No clean images found in {input_dir}.")
    return records


def save_array(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, np.asarray(array, dtype=np.float32))


def _parameter_combinations(
    pair: list[str],
    config: dict[str, Any],
    rng: np.random.Generator,
) -> list[dict[str, SampledDegradation]]:
    parameter_sets = config.get("degradation_parameter_sets")
    if not parameter_sets:
        return [
            {
                name: sample_parameters(name, config["degradations"][name], rng)
                for name in pair
            }
        ]

    options: list[list[dict[str, Any]]] = []
    for name in pair:
        values = parameter_sets.get(name)
        if not isinstance(values, list) or not values:
            raise ValueError(f"Missing non-empty degradation_parameter_sets.{name}")
        options.append([dict(row) for row in values])

    combinations: list[dict[str, SampledDegradation]] = []
    for selected in product(*options):
        sampled: dict[str, SampledDegradation] = {}
        for name, raw_parameters in zip(pair, selected, strict=True):
            parameters = dict(raw_parameters)
            if name in {"noise", "rain"} and "seed" not in parameters:
                parameters["seed"] = int(rng.integers(0, 2**31 - 1))
            sampled[name] = SampledDegradation(name, parameters)
        combinations.append(sampled)
    return combinations


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
    preprocess = str(project.get("image_preprocess", "resize"))

    if args.mock_clean_count > 0:
        clean_records = [
            (f"mock_{index:04d}", make_mock_clean(index, size, seed))
            for index in range(args.mock_clean_count)
        ]
    elif args.input_dir:
        clean_records = load_clean_images(args.input_dir, size, preprocess)
    else:
        raise ValueError("Provide --input-dir or --mock-clean-count.")

    expected_count = project.get("expected_clean_count")
    if expected_count is not None and args.mock_clean_count == 0:
        if len(clean_records) != int(expected_count):
            raise ValueError(
                f"Expected {expected_count} clean images, found {len(clean_records)} in {args.input_dir}."
            )

    data_root = Path(project["data_root"])
    master_rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []

    for clean_id, clean in clean_records:
        save_array(data_root / "clean" / f"{clean_id}.npy", clean)
        for pair in config["degradation_pairs"]:
            pair = list(pair)
            pair_rng = np.random.default_rng(int(master_rng.integers(0, 2**31 - 1)))
            combinations = _parameter_combinations(pair, config, pair_rng)

            for parameter_index, sampled in enumerate(combinations):
                parameter_seed = int(master_rng.integers(0, 2**31 - 1))
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

                    program_id = (
                        f"{clean_id}__{'-'.join(order)}__set{parameter_index:03d}"
                        f"__seed{parameter_seed}"
                    )
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
                        "parameter_set_index": parameter_index,
                        "parameter_seed": parameter_seed,
                        "source_degradations": list(pair),
                        "application_order": list(order),
                        "clean_path": str(clean_path),
                        "source_path": str(source_path),
                        "oracle_mid_paths": oracle_mid_paths,
                        "image_preprocess": preprocess,
                        "image_size": size,
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
