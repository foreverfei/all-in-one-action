"""Serializable degradation programs for counterfactual subset states."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from lineA.degradations import SampledDegradation

DEGRADATION_TO_ACTION = {
    "haze": "dehaze",
    "rain": "derain",
    "lowlight": "enhance",
    "noise": "denoise",
    "motion_blur": "deblur",
}


@dataclass(frozen=True)
class DegradationStep:
    name: str
    order: int
    parameters: dict[str, float | int]
    seed: int | None = None

    def to_sampled(self) -> SampledDegradation:
        params = dict(self.parameters)
        if self.seed is not None and "seed" not in params:
            params["seed"] = self.seed
        return SampledDegradation(self.name, params)

    def to_dict(self) -> dict:
        return {
            "type": self.name,
            "order": self.order,
            "parameters": self.parameters,
            "seed": self.seed,
        }

    @classmethod
    def from_dict(cls, row: dict) -> "DegradationStep":
        return cls(
            str(row["type"]),
            int(row["order"]),
            dict(row["parameters"]),
            row.get("seed"),
        )


@dataclass(frozen=True)
class DegradationProgram:
    program_id: str
    clean_id: str
    steps: tuple[DegradationStep, ...]

    def ordered_steps(self) -> tuple[DegradationStep, ...]:
        return tuple(sorted(self.steps, key=lambda step: step.order))

    def subset(self, keep: Iterable[str]) -> "DegradationProgram":
        keep_set = set(keep)
        selected = [step for step in self.ordered_steps() if step.name in keep_set]
        kept = tuple(
            DegradationStep(step.name, index, dict(step.parameters), step.seed)
            for index, step in enumerate(selected)
        )
        return DegradationProgram(self.program_id, self.clean_id, kept)

    def remove(self, *names: str) -> "DegradationProgram":
        removed = set(names)
        return self.subset(step.name for step in self.steps if step.name not in removed)

    def action_for(self, degradation: str) -> str:
        return DEGRADATION_TO_ACTION[degradation]

    def to_dict(self) -> dict:
        return {
            "program_id": self.program_id,
            "clean_id": self.clean_id,
            "degradation_program": [step.to_dict() for step in self.ordered_steps()],
        }

    @classmethod
    def from_dict(cls, row: dict) -> "DegradationProgram":
        return cls(
            str(row["program_id"]),
            str(row["clean_id"]),
            tuple(DegradationStep.from_dict(step) for step in row["degradation_program"]),
        )


def validate_program(program: DegradationProgram) -> None:
    ordered = program.ordered_steps()
    names = [step.name for step in ordered]
    if len(names) != len(set(names)):
        raise ValueError("A degradation program cannot contain duplicate degradation types.")
    orders = [step.order for step in ordered]
    if orders != list(range(len(orders))):
        raise ValueError(f"Program orders must be contiguous from zero; observed {orders}.")
    for name in names:
        if name not in DEGRADATION_TO_ACTION:
            raise ValueError(f"Unsupported degradation in program: {name}")
