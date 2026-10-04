#!/usr/bin/env bash
# Use distro RPM tools, or the verified local tools retained in an existing cloud snapshot.
set -euo pipefail
cd /workspace/setup/cann
if command -v rpmkeys >/dev/null && command -v rpm2cpio >/dev/null && command -v cpio >/dev/null; then
  cann_rpmkeys=$(command -v rpmkeys)
  cann_rpm2cpio=$(command -v rpm2cpio)
  cann_cpio=$(command -v cpio)
else
  export LD_LIBRARY_PATH=/workspace/setup/cann/tools/usr/lib/x86_64-linux-gnu
  export RPM_CONFIGDIR=/workspace/setup/cann/tools/usr/lib/rpm
  cann_rpmkeys=/workspace/setup/cann/tools/usr/bin/rpmkeys
  cann_rpm2cpio=/workspace/setup/cann/tools/usr/bin/rpm2cpio
  cann_cpio=/workspace/setup/cann/tools/usr/bin/cpio
fi
mkdir -p packages rpmdb
curl -fsSL --retry 2 https://repo.oepkgs.net/ascend/cann/RPM-GPG-KEY-CANN -o RPM-GPG-KEY-CANN
"$cann_rpmkeys" --dbpath /workspace/setup/cann/rpmdb --import RPM-GPG-KEY-CANN
if [ ! -f packages/toolkit-9.2.0-beta.2.rpm ]; then
  curl -fL --retry 2 https://repo.oepkgs.net/ascend/cann/x86_64/Packages/Ascend-cann-toolkit-9.2.0_beta.2-linux.x86_64.rpm -o packages/toolkit-9.2.0-beta.2.rpm.partial
  mv packages/toolkit-9.2.0-beta.2.rpm.partial packages/toolkit-9.2.0-beta.2.rpm
fi
"$cann_rpmkeys" --dbpath /workspace/setup/cann/rpmdb --checksig --verbose packages/toolkit-9.2.0-beta.2.rpm
if [ ! -f rpm-9.2/usr/local/Ascend/Ascend-cann-toolkit_9.2.0-beta.2_linux-x86_64.run ]; then
  mkdir -p rpm-9.2
  "$cann_rpm2cpio" packages/toolkit-9.2.0-beta.2.rpm | (cd rpm-9.2 && "$cann_cpio" -idm --no-absolute-filenames)
fi
if [ ! -d installer-9.2/run_package ]; then
  python3 /workspace/setup/cann/extract_run.py rpm-9.2/usr/local/Ascend/Ascend-cann-toolkit_9.2.0-beta.2_linux-x86_64.run installer-9.2
fi
for cann_component in bisheng-compiler simulator npu-runtime asc-devkit asc-tools ge-executor ge-compiler metadef opbase; do
  if [ ! -f "components-9.2/$cann_component/.verified-extracted" ]; then
    python3 /workspace/setup/cann/extract_run.py "installer-9.2/run_package/cann-${cann_component}_9.2.0-beta.2_linux-x86_64.run" "components-9.2/$cann_component"
    touch "components-9.2/$cann_component/.verified-extracted"
  fi
done
sha256sum -c sysroot-debs/SHA256SUMS
for cann_deb in sysroot-debs/*.deb; do dpkg-deb -x "$cann_deb" /workspace/setup/cann/sysroot; done
python3 /workspace/setup/cann/prepare_prefix.py
source /workspace/setup/tilelang/activate.sh
uv pip install --python /workspace/tilelang/.venv/bin/python /workspace/setup/cann/components-9.2/simulator/x86_64-linux/simulator/bin/cannsim-0.1.0-py3-none-any.whl
source /workspace/setup/cann/activate.sh
bisheng --version
g++ -std=c++17 -O2 /workspace/setup/tilelang/sim_runner.cc \
  -I/workspace/setup/cann/components-9.2/npu-runtime/x86_64-linux/pkg_inc/runtime \
  -I/workspace/setup/cann/components-9.2/npu-runtime/x86_64-linux/pkg_inc \
  -L/workspace/Ascend/cann-9.2.0-beta.2/tools/simulator/Ascend950PR_9589/camodel \
  -Wl,-rpath-link,/workspace/Ascend/cann-9.2.0-beta.2/lib64 \
  -lruntime_camodel -o /workspace/setup/tilelang/sim_runner
