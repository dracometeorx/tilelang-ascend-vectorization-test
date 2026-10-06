// Execute TileLang-produced AIV ELF on the vendor CPU cycle model.
#include <runtime/rt.h>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <vector>
#include <limits>
#include <cstdint>

#define CHECK(call) do { auto rc = (call); if (rc != RT_ERROR_NONE) { \
  std::fprintf(stderr, "%s failed: %d\n", #call, int(rc)); return 1; } } while (0)

int main(int argc, char **argv) {
  if (argc != 5) { std::fprintf(stderr, "Usage: sim_runner kernel.aibin symbol fixture.bin ABO|AO|O|npuir\n"); return 2; }
  if (std::string(argv[4]) != "ABO" && std::string(argv[4]) != "AO" && std::string(argv[4]) != "O" && std::string(argv[4]) != "npuir") return 2;
  std::ifstream fixture(argv[3], std::ios::binary);
  uint32_t sizes[3] = {};
  fixture.read(reinterpret_cast<char*>(sizes), sizeof(sizes));
  for (auto n : sizes) if (n == 0 || n > 65536) return 2;
  std::vector<float> a(sizes[0]), b(sizes[1]), expected(sizes[2]);
  for (auto *values : {&a, &b, &expected})
    fixture.read(reinterpret_cast<char*>(values->data()), values->size()*sizeof(float));
  if (!fixture || fixture.peek() != EOF) return 2;
  const int n = sizes[2];
  constexpr int guard = 64;
  constexpr float canary = -12345.5f;
  std::vector<float> out(n + guard, canary);
  for (int i = 0; i < n; ++i) out[i] = std::numeric_limits<float>::quiet_NaN();
  std::ifstream input(argv[1], std::ios::binary);
  if (!input) return 2;
  std::vector<char> binary((std::istreambuf_iterator<char>(input)), {});
  if (binary.empty()) return 2;
  CHECK(rtSetDevice(0));
  rtStream_t stream;
  CHECK(rtStreamCreate(&stream, 0));
  void *da=nullptr, *db=nullptr, *dc=nullptr;
  const auto abytes = a.size()*sizeof(float), bbytes = b.size()*sizeof(float), bytes = out.size()*sizeof(float);
  CHECK(rtMalloc(&da, abytes, RT_MEMORY_HBM, 0));
  CHECK(rtMalloc(&db, bbytes, RT_MEMORY_HBM, 0));
  CHECK(rtMalloc(&dc, bytes, RT_MEMORY_HBM, 0));
  CHECK(rtMemcpy(da, abytes, a.data(), abytes, RT_MEMCPY_HOST_TO_DEVICE));
  CHECK(rtMemcpy(db, bbytes, b.data(), bbytes, RT_MEMCPY_HOST_TO_DEVICE));
  CHECK(rtMemcpy(dc, bytes, out.data(), bytes, RT_MEMCPY_HOST_TO_DEVICE));
  rtDevBinary_t desc{RT_DEV_BINARY_MAGIC_ELF_AIVEC, 0, binary.data(), binary.size()};
  void *handle=nullptr;
  CHECK(rtDevBinaryRegister(&desc, &handle));
  CHECK(rtFunctionRegister(handle, argv[2], argv[2], argv[2], RT_DEFAULT_KERNEL_MODE));
  std::vector<void*> args;
  for (char c : std::string(argv[4])) {
    if (c == 'A') args.push_back(da);
    if (c == 'B') args.push_back(db);
    if (c == 'O') args.push_back(dc);
  }
  if (std::string(argv[4]) == "npuir") {
    // The CANN 9.2 compiler expands each dynamic rank-1 memref to its
    // allocated/aligned pointers, offset, size and stride. KernelArgSize=232.
    // These one-block workloads have no cross-core/FFTS synchronization or workspace
    // access. CAModel does not implement rtGetC2cCtrlAddr (207000).
    uint64_t ffts_addr = 0;
    struct Memref1D { void *allocated, *aligned; int64_t offset, size, stride; };
    struct NpuirArgs {
      uint64_t ffts;
      Memref1D lock, workspace, a, b, out;
      int32_t grid_x, grid_y, grid_z, pid_x, pid_y, pid_z;
    } npu_args{ffts_addr, {nullptr, nullptr, 0, 0, 1}, {nullptr, nullptr, 0, 0, 1},
        {da, da, 0, sizes[0], 1}, {db, db, 0, sizes[1], 1}, {dc, dc, 0, n, 1}, 1, 1, 1, 0, 0, 0};
    static_assert(sizeof(NpuirArgs) == 232);
    rtArgsEx_t args_info{};
    args_info.args = &npu_args;
    args_info.argsSize = sizeof(npu_args);
    rtTaskCfgInfo_t cfg_info{};
    cfg_info.localMemorySize = 221184;
    CHECK(rtKernelLaunchWithFlagV2(argv[2], 1, &args_info, nullptr, stream, 0, &cfg_info));
  } else {
    CHECK(rtKernelLaunch(argv[2], 1, args.data(), args.size()*sizeof(void*), nullptr, stream));
  }
  CHECK(rtStreamSynchronize(stream));
  CHECK(rtMemcpy(out.data(), bytes, dc, bytes, RT_MEMCPY_DEVICE_TO_HOST));
  for (int i=0; i<n; ++i) {
    if (out[i] != expected[i]) {
      std::fprintf(stderr, "Mismatch at %d: got %g expected %g\n", i, out[i], expected[i]);
      return 1;
    }
  }
  for (int i=n; i<n+guard; ++i) {
    if (out[i] != canary) { std::fprintf(stderr, "Output guard overwritten at %d\n", i); return 1; }
  }
  std::printf("SIMULATOR_CORRECT elements=%d symbol=%s\n", n, argv[2]);
  std::fflush(stdout);
  CHECK(rtDevBinaryUnRegister(handle));
  CHECK(rtFree(da)); CHECK(rtFree(db)); CHECK(rtFree(dc));
  CHECK(rtStreamDestroy(stream));
  CHECK(rtDeviceReset(0));
  return 0;
}
