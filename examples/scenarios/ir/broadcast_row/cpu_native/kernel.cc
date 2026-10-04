// tilelang target: {"kind":"c","tag":"","keys":["cpu"],"host":{"kind":"c","tag":"","keys":["cpu"]}}
#include <tl_templates/cpp/common.h>

#ifdef __cplusplus
extern "C"
#endif
int32_t main_kernel(float* A, float* B, float* O);
#ifdef __cplusplus
extern "C"
#endif
int32_t main_kernel(float* A, float* B, float* O) {
  for (int32_t i = 0; i < 64; ++i) {
    *(float4*)(O + (i * 4)) = (*(float4*)(A + (i * 4)) + *(float4*)(B + ((i & 15) * 4)));
  }
  return 0;
}

