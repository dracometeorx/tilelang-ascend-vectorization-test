#!/usr/bin/env bash
set -euo pipefail
(
  source /workspace/setup/backends/activate_npuir.sh
  python /workspace/setup/backends/npuir_add_lab.py
)
source /workspace/setup/backends/activate.sh
python /workspace/setup/backends/compile_compare.py
python /workspace/setup/backends/simulate_compare.py "$@"
python /workspace/setup/backends/summarize_compare.py
