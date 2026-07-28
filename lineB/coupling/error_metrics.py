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
    """Return a coarse normalized score for exploratory correlation only.

    Formal reports must also use the raw degradation parameters stored in the
    coupling table. This scalar must not replace parameter-wise analyses.
    """

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
        elif step["type"] == "noise":
            values.append(float(parameters["sigma"]) / 50.0)
        elif step["type"] == "motion_blur":
            values.append(float(parameters["length"]) / 17.0)
    return float(np.mean(values)) if values else 0.0
