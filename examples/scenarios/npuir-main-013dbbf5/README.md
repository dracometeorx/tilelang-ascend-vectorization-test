# Fixed new A5 frontend: current evidence (2026-10-06)

14/14 cases compiled and passed independent vendor CAModel simulation, exact values, output canaries and Profiling. No formal failures or reused simulations. The historical multi-backend matrix was not rerun.

- [中文分析](../README.md) / [English analysis](../README.en.md)
- [Current 14-case metrics and evidence](results/): TIR, MLIR, ELF, ABI, compiler command, correctness, Profiling and instruction events.
- [Comparison against historical evidence](comparison.json)
- [Final verification receipt](verification.json), [recovery/build status](preflight.json)
- [Frontend native build receipt](frontend-build.json), [final CMake selections](selected-build-config.json), [device tools and model hashes](device-toolchain.json)
- [Build and reproduction instructions](../../../setup/backends/NPUIR_MAIN.md)
- [Input preparation receipt](inputs.json): immutable preparation-stage `not_run` values, not final status.
- [Diagnostic attempts](probes/), [old-frontend recovery smoke](recovery-smoke-old-frontend/result.json), [old-ELF launch API probe](launch-v2-probe-old-elf/result.json): outside the formal matrix.

The exact A5 dependency commit came from the official public repository. No credential is required for that fetch. Network failures, unsuccessful initial builds/imports and optional diagnostics are retained as history, not current blockers. Actual ABI is 56 bytes, not the discarded 224-byte estimate.

SDKs, virtual environments, compiler shared libraries, full build trees and large simulation traces are excluded. Small generated device ELFs are included. All measurements are simulated; physical A5 execution and a full blank-machine installation remain unverified.
