"""Deterministic smoke-test degradations.

These operators are infrastructure tests, not the final paper degradation protocol.
All images use HWC float32 arrays in [0, 1].
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


@dataclass(frozen=True)
class SampledDegradation:
    name: str
    parameters: dict[str, float | int]


def validate_image(image: np.ndarray) -> np.ndarray:
    array = np.asarray(image, dtype=np.float32)
    if array.ndim != 3 or array.shape[2] != 3:
        raise ValueError(f"Expected HWC RGB image, got shape {array.shape}.")
    if not np.isfinite(array).all():
        raise ValueError("Image contains NaN or Inf.")
    minimum, maximum = float(array.min()), float(array.max())
    if minimum < -1e-6 or maximum > 1.0 + 1e-6:
        raise ValueError(f"Expected range [0,1], got [{minimum:.6f}, {maximum:.6f}].")
    return np.clip(array, 0.0, 1.0)


def _uniform(rng: np.random.Generator, bounds: Sequence[float]) -> float:
    if len(bounds) != 2:
        raise ValueError(f"Expected [min,max], got {bounds}.")
    return float(rng.uniform(float(bounds[0]), float(bounds[1])))


def sample_parameters(
    name: str,
    config: Mapping[str, Any],
    rng: np.random.Generator,
) -> SampledDegradation:
    if name == "haze":
        params = {
            "transmission": _uniform(rng, config["transmission"]),
            "atmospheric_light": _uniform(rng, config["atmospheric_light"]),
        }
    elif name == "rain":
        params = {
            "density": _uniform(rng, config["density"]),
            "length": int(round(_uniform(rng, config["length"]))),
            "angle_deg": _uniform(rng, config["angle_deg"]),
            "opacity": _uniform(rng, config["opacity"]),
            "seed": int(rng.integers(0, 2**31 - 1)),
        }
    elif name == "lowlight":
        params = {
            "gamma": _uniform(rng, config["gamma"]),
            "scale": _uniform(rng, config["scale"]),
        }
    else:
        raise KeyError(f"Unsupported degradation: {name}")
    return SampledDegradation(name=name, parameters=params)


def apply_haze(image: np.ndarray, transmission: float, atmospheric_light: float) -> np.ndarray:
    image = validate_image(image)
    result = image * transmission + atmospheric_light * (1.0 - transmission)
    return np.clip(result, 0.0, 1.0).astype(np.float32)


def apply_lowlight(image: np.ndarray, gamma: float, scale: float) -> np.ndarray:
    image = validate_image(image)
    result = scale * np.power(np.clip(image, 0.0, 1.0), gamma)
    return np.clip(result, 0.0, 1.0).astype(np.float32)


def apply_rain(
    image: np.ndarray,
    density: float,
    length: int,
    angle_deg: float,
    opacity: float,
    seed: int,
) -> np.ndarray:
    image = validate_image(image)
    height, width, _ = image.shape
    rng = np.random.default_rng(seed)
    count = max(1, int(height * width * density / max(length, 1)))

    layer = Image.new("L", (width, height), color=0)
    draw = ImageDraw.Draw(layer)
    angle = np.deg2rad(angle_deg)
    dx = float(np.sin(angle) * length)
    dy = float(np.cos(angle) * length)

    for _ in range(count):
        x0 = float(rng.uniform(0, width))
        y0 = float(rng.uniform(-length, height))
        draw.line((x0, y0, x0 + dx, y0 + dy), fill=255, width=1)

    layer = layer.filter(ImageFilter.GaussianBlur(radius=0.6))
    rain = np.asarray(layer, dtype=np.float32) / 255.0
    result = image + opacity * rain[..., None]
    return np.clip(result, 0.0, 1.0).astype(np.float32)


def apply_degradation(image: np.ndarray, sampled: SampledDegradation) -> np.ndarray:
    if sampled.name == "haze":
        return apply_haze(image, **sampled.parameters)
    if sampled.name == "rain":
        return apply_rain(image, **sampled.parameters)
    if sampled.name == "lowlight":
        return apply_lowlight(image, **sampled.parameters)
    raise KeyError(f"Unsupported degradation: {sampled.name}")


def apply_combination(
    image: np.ndarray,
    sampled_degradations: Sequence[SampledDegradation],
) -> np.ndarray:
    result = validate_image(image)
    for sampled in sampled_degradations:
        result = apply_degradation(result, sampled)
    return result
