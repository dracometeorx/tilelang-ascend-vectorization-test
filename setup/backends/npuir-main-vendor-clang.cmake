# Keep LLVM/Triton objects built with GCC; use vendor Clang for BiShengIR.
# Both use the host libstdc++, the existing ABI macros and C++17 options.
function(npuir_apply_vendor_clang directory)
  get_property(targets DIRECTORY "${directory}" PROPERTY BUILDSYSTEM_TARGETS)
  foreach(target IN LISTS targets)
    set_property(TARGET "${target}" PROPERTY CXX_COMPILER_LAUNCHER
      "/workspace/setup/backends/npuir-main/vendor-clang-launcher.py")
  endforeach()
  get_property(children DIRECTORY "${directory}" PROPERTY SUBDIRECTORIES)
  foreach(child IN LISTS children)
    npuir_apply_vendor_clang("${child}")
  endforeach()
endfunction()
if(CMAKE_CURRENT_SOURCE_DIR STREQUAL CMAKE_SOURCE_DIR)
  cmake_language(DEFER CALL npuir_apply_vendor_clang
    "/workspace/setup/backends/tilelang-mlir-ascend/3rdparty/AscendNPU-IR-Dev/bishengir")
endif()
