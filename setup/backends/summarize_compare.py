"""Summarize verified outputs, retaining provenance and distinct frontend versions."""
import difflib
import html
import json
from pathlib import Path
import re

ROOT = Path('/workspace/setup/tilelang/results')
OUT = ROOT/'backend-comparison'

def main():
    OUT.mkdir(exist_ok=True)
    cases = json.loads((ROOT/'backend-cases.json').read_text())
    for case in cases:
        p = Path(case['directory'])
        log = (p/'compile-passes.log').read_text()
        headers = list(re.finditer(r'^// -----// IR Dump After (.+?) //----- //\n', log, re.M))
        target = p/'backend-passes'
        target.mkdir(exist_ok=True)
        passes = []
        for i, match in enumerate(headers):
            end = headers[i+1].start() if i+1 < len(headers) else len(log)
            name = re.sub(r'[^A-Za-z0-9_.-]+', '_', match[1])
            filename = f'{i:03d}_{name}.mlir'
            (target/filename).write_text(log[match.end():end])
            passes.append({'pass':match[1], 'file':filename})
        (target/'index.json').write_text(json.dumps(passes, indent=2))
    for shape in ['256', '4x64']:
        comparisons = [
            ('npuir-vs-pto-simd', ROOT/'npuir'/shape/'kernel.mlir', ROOT/'pto_probe'/f'{shape}_simd'/'kernel.pto'),
            ('pto-simt-vs-simd', ROOT/'pto_probe'/f'{shape}_simt'/'kernel.pto', ROOT/'pto_probe'/f'{shape}_simd'/'kernel.pto'),
        ]
        for title, left, right in comparisons:
            a,b = left.read_text().splitlines(True), right.read_text().splitlines(True)
            (OUT/f'{shape}_{title}.diff').write_text(''.join(difflib.unified_diff(a,b,fromfile=str(left),tofile=str(right))))
            (OUT/f'{shape}_{title}.html').write_text(difflib.HtmlDiff(wrapcolumn=95).make_file(a,b,fromdesc=html.escape(str(left)),todesc=html.escape(str(right))))
    rows = []
    for case in cases:
        p = Path(case['directory'])/'verified-simulation.json'
        if not p.exists():
            rows.append(f'| {case["backend"]} | {case["shape"]} | {case["mode"]} | 尚未验证 | — | — |')
            continue
        result = json.loads(p.read_text())
        info = result['profile']['kernel_info']
        report = Path(result['archive'])/'report/index.html'
        rows.append(f'| {case["backend"]} | {case["shape"]} | {case["mode"]} | [正确]({report}) | {info["kernel_total_clocks"]} | {info["kernel_instructions_executed"]} |')
    text = '''# NPU-IR / PTO lowering 对比

本实验使用同一语义：单 block，FP32，256 元素，形状 `(256,)` 与 `(4,64)`，`O=A+B`，先 GM→UB，再计算，最后 UB→GM。

| 后端 | 形状 | 计算方式 | CAModel 数值验证 / 报告 | 模拟周期 | 执行指令数 |
|---|---|---|---|---:|---:|
''' + '\n'.join(rows) + '''

## 实际 lowering

**NPU-IR：**独立上游发布 wheel `0.1.1.030+npuir+4e1bb3e4` → `NpuLoopVectorize` → `T.npuir_add` → 高层 `hivm.hir.vadd`（保留 tensor 形状）→ NPU-IR 1.2.0 的 AutoVectorizeV2 / OutlineVectorFunction → bufferization / UB 分配 / HIVMAVE → `hivm_regbaseintrins` / LLVM dialect → Bisheng → A5 ELF。

**PTO：**主 checkout `994b44ec` → AscendLayoutInference / AutoSchedule → SIMT/SIMD T.Parallel lowering → PTODSL → PTO MLIR → PTOAS VMI 0.1.9 / VPTO → LLVM IR → Bisheng → fat object 内的 CCE ELF → 链接后的 A5 ELF。

| 比较项 | NPU-IR（本次 Developer 用例） | PTO SIMT | PTO SIMD |
|---|---|---|---|
| 高层并行表达 | 整块 tensor 的 `hivm.hir.vadd` | `pto.section.simt<<<128,1,1>>>` | `pto.vecscope` / 显式向量操作 |
| FP32 向量宽度何时确定 | NPU-IR 后端向量化时确定为 64 | TileLang 分配每线程 2 元素 | TileLang 已确定每次 64 元素 |
| 256 元素的映射 | 后端生成 4 次向量运算 | 128 线程 × 2 元素 | 4 次 × 64 元素 |
| UB 调度与同步 | NPU-IR 后端执行 | TileLang 先执行，PTO 后续优化 | TileLang 先执行，PTO 后续优化 |
| 本例 UB 数据缓冲 | 2 × 1024 字节，输出复用输入缓冲 | 3 × 1024 字节 | 3 × 1024 字节 |
| 输入参数 ABI | 动态 memref 展开为描述符，232 字节 | 三个 GM 指针，24 字节 | 三个 GM 指针，24 字节 |

## 查看 IR

- `../npuir/{256,4x64}/`：9 个 TIR pass 快照、`kernel.mlir`、`temps/module.hivm.opt.mlir`、`backend-passes/`、完整编译日志、`kernel.o`。
- `../pto_probe/{256,4x64}_{simt,simd}/`：86 个 TIR pass 快照、原始 PTODSL、`kernel.pto`、`kernel.vpto.mlir`、`kernel.ll`、`backend-passes/`、`kernel.aibin`。
- 本目录 HTML 对照可以查看 NPU-IR 与 PTO SIMD，以及 PTO SIMT 与 SIMD。不同 dialect 的文本差异用于定位语义，不是逐 pass 等价证明。
- `backend-passes/index.json` 按实际执行次序索引；只保存编译器报告发生变化的阶段，片段可能处在函数作用域，完整日志保留上下文。

## 复现

```bash
bash /workspace/setup/backends/run.sh
# 仅复用二进制及 runner SHA256 一致、已正确验证的模拟结果：
bash /workspace/setup/backends/run.sh --reuse
```

## 比较边界

1. 两条路径使用不同 TileLang 版本/分支，所以周期差异同时包含前端、布局、UB 复用、函数 ABI 和编译器优化差异，不能概括为某个 IR 普遍更快。
2. 当前 NPU-IR 用例走自动 SIMD；本次没有将其宣称为显式 `T.SimtVF` / `T.SimdVF` 接口验证。PTO 的两个显式作用域均来自主仓库原用例。
3. PTO 原始输出保留。公开 VMI wheel 与主仓库的私有 helper import 不完全匹配；这四个用例经 AST 检查不使用 helper，独立编译副本仅移除未使用 import，diff 已保存。需要 helper 的其他算子不能直接外推。
4. NPU-IR 前端在独立 Python3.11 环境运行，LazyLoader 延迟真实 torch_npu 的运行时导入；编译器和 wheel 文件未修改。发布 wheel 的 Ascend950 白名单有遗漏，本次只验证 FP32 高层 lowering，下游显式指定 Ascend950PR_9589。详见 `/workspace/setup/backends/NPUIR_FRONTEND.md`。
5. 模拟器统一为 CANN9.2 beta.2 Ascend950PR_9589；数值检查使用相同确定性输入、输出初始 NaN，逐元素精确比较。报告周期是模拟结果，不是 CPU 墙钟时间或物理 NPU 实测。
   本次每条路径的 1D 与 2D 最终二进制 SHA256 相同；两次报告的小幅周期差异属于模型运行间波动，不能解释为 1D/2D lowering 的性能差异。
6. 当前 runner 仅用于这些单 block 加法；FFTS/锁/workspace 未使用，传零。CAModel 的 rtGetC2cCtrlAddr 返回不支持，不代表跨核或混合 kernel 可用。
'''
    (OUT/'README.md').write_text(text)
    print(OUT/'README.md')

if __name__ == '__main__':
    main()
