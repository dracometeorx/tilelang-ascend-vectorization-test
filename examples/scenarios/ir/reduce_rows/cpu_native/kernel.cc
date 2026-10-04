// tilelang target: {"kind":"c","tag":"","keys":["cpu"],"host":{"kind":"c","tag":"","keys":["cpu"]}}
#include <tl_templates/cpp/common.h>

#ifdef __cplusplus
extern "C"
#endif
int32_t main_kernel(float* A, float* O);
#ifdef __cplusplus
extern "C"
#endif
int32_t main_kernel(float* A, float* O) {
  for (int32_t i = 0; i < 4; ++i) {
    O[i] = 0.000000e+00f;
    for (int32_t k = 0; k < 64; ++k) {
      O[i] = (O[i] + A[((i * 64) + k)]);
    }
  }
  return 0;
}

