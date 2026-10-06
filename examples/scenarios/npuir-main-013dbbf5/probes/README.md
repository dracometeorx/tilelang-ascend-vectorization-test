# Diagnostic probes, outside the 14-case matrix

These attempts are not included in the formal results. The first copy lowering ran from the test repository directory: TileLang's version suffix used that current directory's Git HEAD (`06d764af`), while the checked import/source/library provenance correctly identified `013dbbf5`. Formal workers run with the frontend repository as their working directory.

- `initial-import-abort`: LLVM option registration conflict before lowering; resolved by hiding static library symbols when linking libtilelangir.so.
- `hardware-query-attempt`: real import succeeded, lowering hit a hardware architecture query in a CPU environment. The harness explicitly selects the fixed A5 architecture cache; no computational operation is mocked.
- `backend-original-flags`: existing BishengIR 1.2.0 returns exit 0, but the ELF lacks a kernel argument section/entry metadata. Rejected as a launchable kernel.
- `backend-a5-flags`: the same backend with the fixed frontend's A5 JIT flags yields a 56-byte kernel ABI; independently simulated copy passed (2155 cycles / 65 instructions). The optional save-linked-ir attempt fails because this SDK Bisheng driver rejects -emit-llvm; it is not the command used for the final ELF.
- `backend-matching-a5-flags`: the newly built dependency compiler rejects --save-temps. It is not used as the device backend for the formal comparison.

Full traces remain local. The matrix contains fresh independent executions, not reused probes.
