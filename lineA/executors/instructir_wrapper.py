"""Strict adapter boundary for an external InstructIR installation.

No InstructIR source code or checkpoint is committed to this repository.
Students only need to implement `load_external_predictor` for the local installation.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import numpy as np

from lineA.executors.base import RestorationExecutor

PredictFunction = Callable[[np.ndarray, str], np.ndarray]


class InstructIRExecutor(RestorationExecutor):
    supported_actions = ("dehaze", "derain", "enhance")

    def __init__(self, predict_fn: PredictFunction, checkpoint: str) -> None:
        self._predict_fn = predict_fn
        self.checkpoint = checkpoint

    def restore(self, image: np.ndarray, action: str) -> np.ndarray:
        array = self._validate(image, action)
        output = np.asarray(self._predict_fn(array, action), dtype=np.float32)
        if output.shape != array.shape:
            raise ValueError(f"Executor changed shape from {array.shape} to {output.shape}.")
        if not np.isfinite(output).all():
            raise ValueError("Executor output contains NaN or Inf.")
        minimum, maximum = float(output.min()), float(output.max())
        if minimum < -1e-4 or maximum > 1.0 + 1e-4:
            raise ValueError(
                f"Executor output must be [0,1]; observed [{minimum:.6f}, {maximum:.6f}]."
            )
        return np.clip(output, 0.0, 1.0).astype(np.float32)

    @classmethod
    def from_external(
        cls,
        external_repo: str | Path,
        checkpoint: str | Path,
        prompts: dict[str, str],
    ) -> "InstructIRExecutor":
        predict_fn = load_external_predictor(Path(external_repo), Path(checkpoint), prompts)
        return cls(predict_fn=predict_fn, checkpoint=str(checkpoint))


def load_external_predictor(
    external_repo: Path,
    checkpoint: Path,
    prompts: dict[str, str],
) -> PredictFunction:
    """Connect the local InstructIR installation.

    Required contract:
      input: HWC float32 RGB in [0,1]
      action: dehaze / derain / enhance
      output: HWC float32 RGB in [0,1]

    Integration checklist:
      1. add `external_repo` to sys.path or install InstructIR as an editable package;
      2. load the checkpoint once, outside the returned function;
      3. call model.eval() and use torch.no_grad();
      4. map `action` through `prompts`;
      5. preserve image size and RGB order;
      6. return CPU float32 NumPy data without uint8/JPEG round trips.
    """
    raise NotImplementedError(
        "InstructIR adapter is not configured. "
        "Follow README section '接入 InstructIR' and implement load_external_predictor(). "
        f"external_repo={external_repo}, checkpoint={checkpoint}, actions={tuple(prompts)}"
    )
