import numpy as np

from lineB.coupling.directed_coupling import compute_directed_coupling


def test_coupling_definition_is_exact() -> None:
    zeros = np.zeros((8, 8, 3), dtype=np.float32)
    actual_mid = np.full_like(zeros, 0.1)
    oracle_successor = np.full_like(zeros, 0.1)
    actual_final = np.full_like(zeros, 0.2)
    reverse_final = np.full_like(zeros, 0.3)

    result = compute_directed_coupling(
        actual_mid=actual_mid,
        oracle_mid=zeros,
        oracle_successor=oracle_successor,
        actual_final=actual_final,
        final_target=zeros,
        reverse_actual_final=reverse_final,
    )

    assert result.decomposition_error < 1e-15
    assert abs(
        result.signed_coupling
        - (result.actual_path_error - result.successor_intrinsic_error)
    ) < 1e-15
