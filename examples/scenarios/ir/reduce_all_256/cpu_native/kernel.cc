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
  O[0] = 0.000000e+00f;
  for (int32_t k = 0; k < 256; ++k) {
    O[0] = (O[0] + A[k]);
  }
  return 0;
}

