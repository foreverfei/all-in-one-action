import numpy as np

from lineA.degradation_program import DegradationProgram, DegradationStep
from lineA.lattice_renderer import render_program, render_subset


def test_subset_keeps_remaining_parameters() -> None:
    clean = np.full((12, 12, 3), 0.4, dtype=np.float32)
    program = DegradationProgram(
        "program",
        "clean",
        (
            DegradationStep(
                "haze",
                0,
                {"transmission": 0.5, "atmospheric_light": 0.9},
            ),
            DegradationStep(
                "lowlight",
                1,
                {"gamma": 2.0, "scale": 0.7},
            ),
        ),
    )

    subset = render_subset(clean, program, {"lowlight"})
    expected = render_program(clean, program.subset({"lowlight"}))
    assert np.allclose(subset, expected)
