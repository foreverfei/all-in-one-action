#!/usr/bin/env bash
set -euo pipefail

CONFIG="${1:-configs/pilot_noise_blur.yaml}"

python tools/check_experiment_paths.py --config "${CONFIG}"

python -m lineA.scripts.generate_week2_states \
  --config "${CONFIG}" \
  --mock-clean-count 2

python -m lineA.scripts.generate_week2_rollouts \
  --config "${CONFIG}" \
  --executor mock

python -m lineA.scripts.check_week2_integrity \
  --config "${CONFIG}"

python -m lineB.scripts.build_week2_coupling_table \
  --config "${CONFIG}"

python -m lineB.scripts.analyze_directionality \
  --config "${CONFIG}"

python -m lineB.scripts.analyze_state_dependence \
  --config "${CONFIG}"

python -m lineB.scripts.analyze_order_baselines \
  --config "${CONFIG}"

pytest -q

echo "Formal protocol mock smoke test completed."
