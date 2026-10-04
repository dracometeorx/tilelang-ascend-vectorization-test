#!/usr/bin/env bash
set -euo pipefail
source /workspace/setup/tilelang/activate.sh
cd /workspace/tilelang
python /workspace/setup/tilelang/add_lab.py
source /workspace/setup/cann/activate.sh
python /workspace/setup/tilelang/simulate.py
python /workspace/setup/tilelang/summarize.py
