from lineA.degradation_program import DegradationProgram, DegradationStep


def test_order_and_direction_mapping() -> None:
    program = DegradationProgram(
        "program",
        "clean",
        (
            DegradationStep(
                "rain",
                0,
                {
                    "density": 0.01,
                    "length": 10,
                    "angle_deg": 0,
                    "opacity": 0.2,
                    "seed": 1,
                },
                1,
            ),
            DegradationStep(
                "haze",
                1,
                {"transmission": 0.5, "atmospheric_light": 0.9},
            ),
        ),
    )

    assert [step.name for step in program.ordered_steps()] == ["rain", "haze"]
    assert program.action_for("rain") == "derain"
    assert program.action_for("haze") == "dehaze"
