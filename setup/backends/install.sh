#!/usr/bin/env bash
set -euo pipefail
# Requires the verified CANN toolkit installed by /workspace/setup/cann/install.sh.
backend_root=/workspace/setup/backends
cann_root=/workspace/setup/cann
for backend_component in npu-ir pto-isa pto-as; do
  case "$backend_component" in
    npu-ir) backend_archive=ascendnpu-ir_1.2.0_linux-x86.run ;;
    *) backend_archive=cann-${backend_component}_9.2.0-beta.2_linux-x86_64.run ;;
  esac
  if [ ! -f "$cann_root/components-9.2/$backend_component/.verified-extracted" ]; then
    python3 "$cann_root/extract_run.py" "$cann_root/installer-9.2/run_package/$backend_archive" "$cann_root/components-9.2/$backend_component"
    touch "$cann_root/components-9.2/$backend_component/.verified-extracted"
  fi
done
backend_wheel=ptoas_vmi-0.1.9-cp312-cp312-manylinux_2_34_x86_64.whl
if [ ! -f "$cann_root/packages/$backend_wheel" ]; then
  curl -fL --retry 2 "https://github.com/hw-native-sys/PTOAS/releases/download/vmi-v0.1.9/$backend_wheel" -o "$cann_root/packages/$backend_wheel"
fi
echo "475b981525f5a1129f7ab89a63670da8375bd00a4e4764dd796b7bea02ac0a35  $cann_root/packages/$backend_wheel" | sha256sum --check
source /workspace/setup/tilelang/activate.sh
uv pip install --python /workspace/tilelang/.venv/bin/python "$cann_root/packages/$backend_wheel"
python "$backend_root/prepare_prefix.py"
source "$backend_root/activate.sh"
ptoas --version
bishengir-compile --version
backend_runner_tmp=$(mktemp "$backend_root/sim_runner_ir.XXXXXX")
trap 'rm -f "$backend_runner_tmp"' EXIT
g++ -std=c++17 -O2 -Wno-deprecated-declarations "$backend_root/sim_runner_ir.cc" \
  -I"$cann_root/components-9.2/npu-runtime/x86_64-linux/pkg_inc/runtime" \
  -I"$cann_root/components-9.2/npu-runtime/x86_64-linux/pkg_inc" \
  -L/workspace/Ascend/cann-9.2.0-beta.2/tools/simulator/Ascend950PR_9589/camodel \
  -Wl,-rpath-link,/workspace/Ascend/cann-9.2.0-beta.2/lib64 \
  -lruntime_camodel -o "$backend_runner_tmp"
if ! cmp -s "$backend_runner_tmp" "$backend_root/sim_runner_ir"; then
  mv "$backend_runner_tmp" "$backend_root/sim_runner_ir"
fi
bash "$backend_root/install_npuir_frontend.sh"
