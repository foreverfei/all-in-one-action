"""Directed predecessor-induced excess-error decomposition."""
from __future__ import annotations

from dataclasses import dataclass

from lineB.coupling.error_metrics import mean_charbonnier


@dataclass(frozen=True)
class CouplingResult:
    mid_error: float
    successor_intrinsic_error: float
    actual_path_error: float
    signed_coupling: float
    harmful_coupling: float
    non_commutativity: float
    decomposition_error: float


def compute_directed_coupling(
    *,
    actual_mid,
    oracle_mid,
    oracle_successor,
    actual_final,
    final_target,
    reverse_actual_final,
    epsilon: float = 1e-3,
) -> CouplingResult:
    mid_error = mean_charbonnier(actual_mid, oracle_mid, epsilon)
    successor_intrinsic_error = mean_charbonnier(
        oracle_successor,
        final_target,
        epsilon,
    )
    actual_path_error = mean_charbonnier(actual_final, final_target, epsilon)
    signed_coupling = actual_path_error - successor_intrinsic_error
    harmful_coupling = max(signed_coupling, 0.0)
    non_commutativity = mean_charbonnier(
        actual_final,
        reverse_actual_final,
        epsilon,
    )
    decomposition_error = abs(
        signed_coupling - (actual_path_error - successor_intrinsic_error)
    )
    return CouplingResult(
        mid_error=mid_error,
        successor_intrinsic_error=successor_intrinsic_error,
        actual_path_error=actual_path_error,
        signed_coupling=signed_coupling,
        harmful_coupling=harmful_coupling,
        non_commutativity=non_commutativity,
        decomposition_error=decomposition_error,
    )
