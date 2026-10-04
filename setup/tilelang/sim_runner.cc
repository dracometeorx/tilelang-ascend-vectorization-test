// Execute TileLang-produced AIV ELF on the vendor CPU cycle model.
#include <runtime/rt.h>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <vector>
#include <limits>

#define CHECK(call) do { auto rc = (call); if (rc != RT_ERROR_NONE) { \
  std::fprintf(stderr, "%s failed: %d\n", #call, int(rc)); return 1; } } while (0)

int main(int argc, char **argv) {
  if (argc != 4) { std::fprintf(stderr, "Usage: sim_runner kernel.aibin symbol elements\n"); return 2; }
  const int n = std::atoi(argv[3]);
  if (n <= 0 || n > 65536) return 2;
  std::ifstream input(argv[1], std::ios::binary);
  if (!input) return 2;
  std::vector<char> binary((std::istreambuf_iterator<char>(input)), {});
  if (binary.empty()) return 2;
  CHECK(rtSetDevice(0));
  rtStream_t stream;
  CHECK(rtStreamCreate(&stream, 0));
  std::vector<float> a(n), b(n), out(n, std::numeric_limits<float>::quiet_NaN());
  for (int i=0; i<n; ++i) { a[i] = float(i % 31 - 15) * 0.25f; b[i] = float(i % 17 - 8) * 0.5f; }
  void *da=nullptr, *db=nullptr, *dc=nullptr;
  const auto bytes = n * sizeof(float);
  CHECK(rtMalloc(&da, bytes, RT_MEMORY_HBM, 0));
  CHECK(rtMalloc(&db, bytes, RT_MEMORY_HBM, 0));
  CHECK(rtMalloc(&dc, bytes, RT_MEMORY_HBM, 0));
  CHECK(rtMemcpy(da, bytes, a.data(), bytes, RT_MEMCPY_HOST_TO_DEVICE));
  CHECK(rtMemcpy(db, bytes, b.data(), bytes, RT_MEMCPY_HOST_TO_DEVICE));
  CHECK(rtMemcpy(dc, bytes, out.data(), bytes, RT_MEMCPY_HOST_TO_DEVICE));
  rtDevBinary_t desc{RT_DEV_BINARY_MAGIC_ELF_AIVEC, 0, binary.data(), binary.size()};
  void *handle=nullptr;
  CHECK(rtDevBinaryRegister(&desc, &handle));
  CHECK(rtFunctionRegister(handle, argv[2], argv[2], argv[2], RT_DEFAULT_KERNEL_MODE));
  void *args[] = {da, db, dc};
  CHECK(rtKernelLaunch(argv[2], 1, args, sizeof(args), nullptr, stream));
  CHECK(rtStreamSynchronize(stream));
  CHECK(rtMemcpy(out.data(), bytes, dc, bytes, RT_MEMCPY_DEVICE_TO_HOST));
  for (int i=0; i<n; ++i) {
    if (out[i] != a[i] + b[i]) {
      std::fprintf(stderr, "Mismatch at %d: got %g expected %g\n", i, out[i], a[i]+b[i]);
      return 1;
    }
  }
  std::printf("SIMULATOR_CORRECT elements=%d symbol=%s\n", n, argv[2]);
  std::fflush(stdout);
  CHECK(rtDevBinaryUnRegister(handle));
  CHECK(rtFree(da)); CHECK(rtFree(db)); CHECK(rtFree(dc));
  CHECK(rtStreamDestroy(stream));
  CHECK(rtDeviceReset(0));
  return 0;
}
