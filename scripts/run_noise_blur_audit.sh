#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "Usage: $0 <config.yaml> <clean-image-dir> [mock|instructir]" >&2
  exit 2
fi

CONFIG="$1"
INPUT_DIR="$2"
EXECUTOR="${3:-instructir}"

python -m lineA.scripts.generate_week2_states \
  --config "${CONFIG}" \
  --input-dir "${INPUT_DIR}"

python -m lineA.scripts.generate_week2_rollouts \
  --config "${CONFIG}" \
  --executor "${EXECUTOR}"

python -m lineA.scripts.check_week2_integrity \
  --config "${CONFIG}"

python -m lineB.scripts.build_week2_coupling_table \
  --config "${CONFIG}"

python -m lineB.scripts.analyze_directionality \
  --config "${CONFIG}"

python -m lineB.scripts.analyze_state_dependence \
  --config "${CONFIG}"

pytest -q

echo "Completed directed coupling audit: config=${CONFIG}, executor=${EXECUTOR}"
