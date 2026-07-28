"""Render full and subset states while preserving sampled degradation variables."""
from __future__ import annotations

import numpy as np

from lineA.degradation_program import DegradationProgram, validate_program
from lineA.degradations import apply_combination, validate_image


def render_program(clean: np.ndarray, program: DegradationProgram) -> np.ndarray:
    validate_program(program)
    sampled = [step.to_sampled() for step in program.ordered_steps()]
    return apply_combination(validate_image(clean), sampled)


def render_subset(
    clean: np.ndarray,
    program: DegradationProgram,
    keep: set[str],
) -> np.ndarray:
    return render_program(clean, program.subset(keep))


def render_without(
    clean: np.ndarray,
    program: DegradationProgram,
    *remove: str,
) -> np.ndarray:
    return render_program(clean, program.remove(*remove))
