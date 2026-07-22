import numpy as np

from lineB.scripts.build_week1_labels import add, subtract


def test_two_step_identity_is_exact_by_definition() -> None:
    q_x = {"psnr": 10.0, "neg_lpips": -0.8, "neg_dists": -0.6}
    q_a = {"psnr": 13.0, "neg_lpips": -0.5, "neg_dists": -0.4}
    q_b = {"psnr": 12.0, "neg_lpips": -0.6, "neg_dists": -0.5}
    q_ab = {"psnr": 16.0, "neg_lpips": -0.3, "neg_dists": -0.2}

    gain_a = subtract(q_a, q_x)
    gain_b = subtract(q_b, q_x)
    influence = add(
        q_ab,
        {key: -value for key, value in q_a.items()},
        {key: -value for key, value in q_b.items()},
        q_x,
    )

    lhs = subtract(q_ab, q_x)
    rhs = add(gain_a, gain_b, influence)

    for key in lhs:
        assert np.isclose(lhs[key], rhs[key], atol=1e-12)


def test_influence_can_be_directional() -> None:
    eta_a_to_b = 1.0
    eta_b_to_a = -0.5
    assert eta_a_to_b != eta_b_to_a
