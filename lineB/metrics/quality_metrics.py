"""Unified full-reference image-quality metrics.

Input arrays are HWC RGB float32 in [0,1].
Returned distances preserve their native direction:
  PSNR: higher is better
  LPIPS/DISTS: lower is better
The label builder converts them to [PSNR, -LPIPS, -DISTS].
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np


def validate_pair(prediction: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    prediction = np.asarray(prediction, dtype=np.float32)
    target = np.asarray(target, dtype=np.float32)
    if prediction.shape != target.shape:
        raise ValueError(f"Shape mismatch: {prediction.shape} vs {target.shape}.")
    if prediction.ndim != 3 or prediction.shape[2] != 3:
        raise ValueError(f"Expected HWC RGB arrays, got {prediction.shape}.")
    for name, array in (("prediction", prediction), ("target", target)):
        if not np.isfinite(array).all():
            raise ValueError(f"{name} contains NaN/Inf.")
        if float(array.min()) < -1e-6 or float(array.max()) > 1.0 + 1e-6:
            raise ValueError(f"{name} is outside [0,1].")
    return np.clip(prediction, 0, 1), np.clip(target, 0, 1)


def psnr(prediction: np.ndarray, target: np.ndarray, data_range: float = 1.0) -> float:
    prediction, target = validate_pair(prediction, target)
    mse = float(np.mean((prediction.astype(np.float64) - target.astype(np.float64)) ** 2))
    if mse == 0.0:
        return float("inf")
    return float(10.0 * np.log10((data_range**2) / mse))


class QualityEvaluator:
    def __init__(self, metrics: Iterable[str]) -> None:
        self.metrics = tuple(metric.strip().lower() for metric in metrics)
        unknown = set(self.metrics) - {"psnr", "lpips", "dists"}
        if unknown:
            raise ValueError(f"Unknown metrics: {sorted(unknown)}")
        self._lpips_model = None
        self._dists_model = None

    def _to_torch(self, image: np.ndarray):
        try:
            import torch
        except ImportError as exc:
            raise RuntimeError("Install PyTorch before using LPIPS or DISTS.") from exc
        tensor = torch.from_numpy(np.asarray(image, dtype=np.float32))
        return tensor.permute(2, 0, 1).unsqueeze(0)

    def _lpips(self, prediction: np.ndarray, target: np.ndarray) -> float:
        try:
            import lpips
            import torch
        except ImportError as exc:
            raise RuntimeError("Install optional dependency: pip install lpips") from exc
        if self._lpips_model is None:
            self._lpips_model = lpips.LPIPS(net="alex").eval()
        prediction_t = self._to_torch(prediction) * 2.0 - 1.0
        target_t = self._to_torch(target) * 2.0 - 1.0
        with torch.no_grad():
            return float(self._lpips_model(prediction_t, target_t).item())

    def _dists(self, prediction: np.ndarray, target: np.ndarray) -> float:
        try:
            import torch
            from DISTS_pytorch import DISTS
        except ImportError as exc:
            raise RuntimeError(
                "Install DISTS from https://github.com/dingkeyan93/DISTS"
            ) from exc
        if self._dists_model is None:
            self._dists_model = DISTS().eval()
        prediction_t = self._to_torch(prediction)
        target_t = self._to_torch(target)
        with torch.no_grad():
            return float(self._dists_model(prediction_t, target_t).item())

    def evaluate(self, prediction: np.ndarray, target: np.ndarray) -> dict[str, float]:
        prediction, target = validate_pair(prediction, target)
        results: dict[str, float] = {}
        for metric in self.metrics:
            if metric == "psnr":
                results["psnr"] = psnr(prediction, target)
            elif metric == "lpips":
                results["lpips"] = self._lpips(prediction, target)
            elif metric == "dists":
                results["dists"] = self._dists(prediction, target)
        return results

    def quality_vector(self, prediction: np.ndarray, target: np.ndarray) -> dict[str, float]:
        raw = self.evaluate(prediction, target)
        vector: dict[str, float] = {}
        if "psnr" in raw:
            vector["psnr"] = raw["psnr"]
        if "lpips" in raw:
            vector["neg_lpips"] = -raw["lpips"]
        if "dists" in raw:
            vector["neg_dists"] = -raw["dists"]
        return vector
