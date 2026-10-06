#!/usr/bin/env python3
"""Use the installed vendor Clang for pinned BiShengIR host sources."""
import os
import sys
compiler = "/workspace/Ascend/cann-9.2.0-beta.2/tools/bisheng_compiler/bin/bisheng"
gcc_only = {"-fno-lifetime-dse", "-Wno-maybe-uninitialized", "-Wno-class-memaccess"}
args = [a for a in sys.argv[2:] if a not in gcc_only]
os.execv(compiler, [compiler, *args])
