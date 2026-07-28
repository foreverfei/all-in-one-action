"""Deterministic degradation operators used by the controlled experiments.

The original haze/rain/low-light operators are retained for the Week-1/Week-2
infrastructure experiments. Gaussian noise and linear motion blur are added for
the formal noise-blur coupling protocol.

All images use HWC float32 RGB arrays in [0, 1].
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import convolve


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


def _scalar_or_uniform(value: Any, rng: np.random.Generator) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return _uniform(rng, value)


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
    elif name == "noise":
        params = {
            "sigma": _scalar_or_uniform(config["sigma"], rng),
            "seed": int(rng.integers(0, 2**31 - 1)),
        }
    elif name == "motion_blur":
        length = int(round(_scalar_or_uniform(config["length"], rng)))
        params = {
            "length": length if length % 2 == 1 else length + 1,
            "angle_deg": _scalar_or_uniform(config["angle_deg"], rng),
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


def apply_noise(image: np.ndarray, sigma: float, seed: int) -> np.ndarray:
    """Apply additive white Gaussian noise.

    ``sigma`` is expressed in the conventional 8-bit intensity scale, e.g.
    sigma=25 corresponds to a standard deviation of 25/255 in [0,1].
    """

    image = validate_image(image)
    if sigma < 0:
        raise ValueError(f"Noise sigma must be non-negative, got {sigma}.")
    rng = np.random.default_rng(int(seed))
    noise = rng.normal(0.0, float(sigma) / 255.0, size=image.shape).astype(np.float32)
    return np.clip(image + noise, 0.0, 1.0).astype(np.float32)


def make_motion_blur_kernel(length: int, angle_deg: float) -> np.ndarray:
    """Create a normalized odd-sized linear motion-blur kernel."""

    length = int(length)
    if length < 3:
        raise ValueError(f"Motion-blur length must be >=3, got {length}.")
    if length % 2 == 0:
        length += 1

    radius = length // 2
    yy, xx = np.mgrid[-radius : radius + 1, -radius : radius + 1].astype(np.float32)
    angle = np.deg2rad(float(angle_deg))
    direction_x = np.cos(angle)
    direction_y = np.sin(angle)
    projection = xx * direction_x + yy * direction_y
    perpendicular = -xx * direction_y + yy * direction_x
    mask = (np.abs(perpendicular) <= 0.5) & (np.abs(projection) <= radius + 0.5)
    kernel = mask.astype(np.float32)
    if float(kernel.sum()) == 0.0:
        kernel[radius, radius] = 1.0
    kernel /= float(kernel.sum())
    return kernel


def apply_motion_blur(image: np.ndarray, length: int, angle_deg: float) -> np.ndarray:
    image = validate_image(image)
    kernel = make_motion_blur_kernel(length, angle_deg)
    channels = [convolve(image[..., channel], kernel, mode="reflect") for channel in range(3)]
    result = np.stack(channels, axis=-1)
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
    if sampled.name == "noise":
        return apply_noise(image, **sampled.parameters)
    if sampled.name == "motion_blur":
        return apply_motion_blur(image, **sampled.parameters)
    raise KeyError(f"Unsupported degradation: {sampled.name}")


def apply_combination(
    image: np.ndarray,
    sampled_degradations: Sequence[SampledDegradation],
) -> np.ndarray:
    result = validate_image(image)
    for sampled in sampled_degradations:
        result = apply_degradation(result, sampled)
    return result
