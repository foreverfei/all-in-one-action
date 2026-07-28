"""Primary error space for directed coupling audit."""
from __future__ import annotations

import numpy as np

from lineB.metrics.quality_metrics import validate_pair


def mean_charbonnier(
    prediction: np.ndarray,
    target: np.ndarray,
    epsilon: float = 1e-3,
) -> float:
    prediction, target = validate_pair(prediction, target)
    difference = prediction.astype(np.float64) - target.astype(np.float64)
    return float(np.mean(np.sqrt(difference * difference + epsilon * epsilon)))


def severity_score(metadata: dict) -> float:
    values: list[float] = []
    for step in metadata.get("degradation_program", []):
        parameters = step.get("parameters", {})
        if step["type"] == "haze":
            values.append(1.0 - float(parameters["transmission"]))
        elif step["type"] == "rain":
            values.append(
                float(parameters["density"]) * 20.0 + float(parameters["opacity"])
            )
        elif step["type"] == "lowlight":
            values.append(
                float(parameters["gamma"]) - 1.0 + 1.0 - float(parameters["scale"])
            )
    return float(np.mean(values)) if values else 0.0
