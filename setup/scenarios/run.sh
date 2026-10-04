#!/usr/bin/env bash
set -euo pipefail
source /workspace/setup/backends/activate.sh
python /workspace/setup/scenarios/suite.py "$@"
