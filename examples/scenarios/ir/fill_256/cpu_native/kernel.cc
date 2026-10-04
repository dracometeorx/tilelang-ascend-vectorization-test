// tilelang target: {"kind":"c","tag":"","keys":["cpu"],"host":{"kind":"c","tag":"","keys":["cpu"]}}
#include <tl_templates/cpp/common.h>

#ifdef __cplusplus
extern "C"
#endif
int32_t main_kernel(float* O);
#ifdef __cplusplus
extern "C"
#endif
int32_t main_kernel(float* O) {
  for (int32_t i = 0; i < 64; ++i) {
    float broadcast_var = 1.250000e+00f;
    *(float4*)(O + (i * 4)) = ((float4)(broadcast_var, broadcast_var, broadcast_var, broadcast_var));
  }
  return 0;
}

