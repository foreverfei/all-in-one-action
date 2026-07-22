"""Executor interfaces used by the rollout pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


class RestorationExecutor(ABC):
    """Map an HWC float32 RGB image and action name to a restored image."""

    supported_actions: tuple[str, ...] = ()

    @abstractmethod
    def restore(self, image: np.ndarray, action: str) -> np.ndarray:
        raise NotImplementedError

    def _validate(self, image: np.ndarray, action: str) -> np.ndarray:
        array = np.asarray(image, dtype=np.float32)
        if action not in self.supported_actions:
            raise ValueError(f"Unsupported action {action!r}; expected {self.supported_actions}.")
        if array.ndim != 3 or array.shape[2] != 3:
            raise ValueError(f"Expected HWC RGB image, got {array.shape}.")
        if not np.isfinite(array).all():
            raise ValueError("Input contains NaN or Inf.")
        if float(array.min()) < -1e-6 or float(array.max()) > 1.0 + 1e-6:
            raise ValueError("Input must be in [0,1].")
        return np.clip(array, 0.0, 1.0)


class MockExecutor(RestorationExecutor):
    """Deterministic executor for infrastructure tests only.

    This class is not a scientific restoration baseline.
    """

    supported_actions = ("dehaze", "derain", "enhance")

    def restore(self, image: np.ndarray, action: str) -> np.ndarray:
        array = self._validate(image, action)
        pil = Image.fromarray(np.round(array * 255.0).astype(np.uint8), mode="RGB")

        if action == "dehaze":
            output = ImageEnhance.Contrast(pil).enhance(1.25)
        elif action == "derain":
            output = pil.filter(ImageFilter.MedianFilter(size=3))
        elif action == "enhance":
            output = ImageEnhance.Brightness(pil).enhance(1.20)
        else:
            raise AssertionError(action)

        result = np.asarray(output, dtype=np.float32) / 255.0
        return np.clip(result, 0.0, 1.0).astype(np.float32)
