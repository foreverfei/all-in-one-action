from __future__ import annotations

import numpy as np

from lineA.degradations import (
    SampledDegradation,
    apply_combination,
    apply_motion_blur,
    apply_noise,
    make_motion_blur_kernel,
)
from lineA.scripts.generate_week2_states import _parameter_combinations


def gradient_image(size: int = 32) -> np.ndarray:
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    image = np.stack(
        [xx / (size - 1), yy / (size - 1), (xx + yy) / (2 * (size - 1))],
        axis=-1,
    )
    return image.astype(np.float32)


def test_gaussian_noise_is_seed_deterministic() -> None:
    image = gradient_image()
    first = apply_noise(image, sigma=25, seed=7)
    second = apply_noise(image, sigma=25, seed=7)
    third = apply_noise(image, sigma=25, seed=8)
    assert np.array_equal(first, second)
    assert not np.array_equal(first, third)
    assert first.dtype == np.float32
    assert 0.0 <= float(first.min()) <= float(first.max()) <= 1.0


def test_motion_blur_kernel_is_normalized() -> None:
    kernel = make_motion_blur_kernel(length=9, angle_deg=30)
    assert kernel.shape == (9, 9)
    assert np.isclose(kernel.sum(), 1.0)
    assert np.count_nonzero(kernel) > 1


def test_motion_blur_preserves_shape_and_range() -> None:
    image = gradient_image()
    result = apply_motion_blur(image, length=17, angle_deg=-30)
    assert result.shape == image.shape
    assert result.dtype == np.float32
    assert 0.0 <= float(result.min()) <= float(result.max()) <= 1.0


def test_noise_and_blur_application_orders_are_explicit() -> None:
    image = gradient_image()
    noise = SampledDegradation("noise", {"sigma": 50, "seed": 17})
    blur = SampledDegradation("motion_blur", {"length": 17, "angle_deg": 30})
    noise_then_blur = apply_combination(image, [noise, blur])
    blur_then_noise = apply_combination(image, [blur, noise])
    assert not np.allclose(noise_then_blur, blur_then_noise)


def test_formal_parameter_grid_has_twelve_combinations() -> None:
    config = {
        "degradation_parameter_sets": {
            "noise": [{"sigma": 15}, {"sigma": 25}, {"sigma": 50}],
            "motion_blur": [
                {"length": 9, "angle_deg": -30},
                {"length": 9, "angle_deg": 30},
                {"length": 17, "angle_deg": -30},
                {"length": 17, "angle_deg": 30},
            ],
        }
    }
    combinations = _parameter_combinations(
        ["noise", "motion_blur"],
        config,
        np.random.default_rng(2026),
    )
    assert len(combinations) == 12
    assert all("seed" in item["noise"].parameters for item in combinations)
