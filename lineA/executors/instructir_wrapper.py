"""Adapter for the official mv-lab/InstructIR inference structure.

No InstructIR source code or checkpoint is committed to this repository.
The adapter imports a local checkout and follows the official `predict.py` path:
`eval5d.yml` -> image model -> language model -> LM head -> restored image.
"""

from __future__ import annotations

import importlib
import sys
from collections.abc import Callable
from pathlib import Path

import numpy as np
import yaml

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
        config_file: str | Path,
        image_checkpoint: str | Path,
        lm_head_checkpoint: str | Path,
        prompts: dict[str, str],
        device: str = "auto",
    ) -> "InstructIRExecutor":
        predict_fn = load_external_predictor(
            external_repo=Path(external_repo),
            config_file=Path(config_file),
            image_checkpoint=Path(image_checkpoint),
            lm_head_checkpoint=Path(lm_head_checkpoint),
            prompts=prompts,
            device=device,
        )
        checkpoint_name = f"image={image_checkpoint};lm_head={lm_head_checkpoint}"
        return cls(predict_fn=predict_fn, checkpoint=checkpoint_name)


def _require_path(path: Path, description: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Missing {description}: {resolved}")
    return resolved


def load_external_predictor(
    external_repo: Path,
    config_file: Path,
    image_checkpoint: Path,
    lm_head_checkpoint: Path,
    prompts: dict[str, str],
    device: str = "auto",
) -> PredictFunction:
    """Load official InstructIR components once and return a NumPy prediction function.

    Contract:
      input: HWC float32 RGB in [0,1]
      action: dehaze / derain / enhance
      output: HWC float32 RGB in [0,1]
    """
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("Install the PyTorch environment required by InstructIR.") from exc

    repo = _require_path(external_repo, "InstructIR repository")
    config_path = _require_path(config_file, "InstructIR config")
    image_ckpt = _require_path(image_checkpoint, "InstructIR image checkpoint")
    lm_ckpt = _require_path(lm_head_checkpoint, "InstructIR LM-head checkpoint")

    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))

    try:
        utils = importlib.import_module("utils")
        instructir = importlib.import_module("models.instructir")
        text_models = importlib.import_module("text.models")
    except ImportError as exc:
        raise RuntimeError(
            f"Could not import the official InstructIR checkout at {repo}. "
            "Verify that `models/`, `text/`, and `utils.py` exist."
        ) from exc

    with config_path.open("r", encoding="utf-8") as handle:
        cfg = utils.dict2namespace(yaml.safe_load(handle))

    if device == "auto":
        torch_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        torch_device = torch.device(device)

    torch.backends.cudnn.deterministic = True
    model = instructir.create_model(
        input_channels=cfg.model.in_ch,
        width=cfg.model.width,
        enc_blks=cfg.model.enc_blks,
        middle_blk_num=cfg.model.middle_blk_num,
        dec_blks=cfg.model.dec_blks,
        txtdim=cfg.model.textdim,
    ).to(torch_device)
    model.load_state_dict(torch.load(image_ckpt, map_location="cpu"), strict=True)
    model.eval()

    language_model = text_models.LanguageModel(model=cfg.llm.model)
    language_model.eval()
    lm_head = text_models.LMHead(
        embedding_dim=cfg.llm.model_dim,
        hidden_dim=cfg.llm.embd_dim,
        num_classes=cfg.llm.nclasses,
    )
    lm_head.load_state_dict(torch.load(lm_ckpt, map_location="cpu"), strict=True)
    lm_head.eval()

    missing_prompts = set(InstructIRExecutor.supported_actions) - set(prompts)
    if missing_prompts:
        raise KeyError(f"Missing action prompts: {sorted(missing_prompts)}")

    def predict(image: np.ndarray, action: str) -> np.ndarray:
        if action not in prompts:
            raise KeyError(f"No prompt configured for action {action!r}.")
        image_tensor = (
            torch.from_numpy(np.asarray(image, dtype=np.float32))
            .permute(2, 0, 1)
            .unsqueeze(0)
            .to(torch_device)
        )
        with torch.no_grad():
            language_embedding = language_model(prompts[action])
            text_embedding, _ = lm_head(language_embedding)
            restored = model(image_tensor, text_embedding.to(torch_device))
        output = restored[0].permute(1, 2, 0).detach().cpu().numpy()
        return np.clip(output, 0.0, 1.0).astype(np.float32)

    return predict
