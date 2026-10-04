"""Link the latest validated simulation artifacts without re-running kernels."""
import json
from pathlib import Path

root = Path('/workspace/setup/tilelang/results')
records = json.loads((root/'simulation-summary.json').read_text())
assert len(records) == 4
rows = ['# A5 CPU 模拟验证结果', '',
        'CANN 9.2.0 beta.2，Ascend950PR_9589 / dav-3510，FP32 加法。四项数值校验均通过。', '',
        '下列数据来自厂商 CAModel 的本次执行，属于模拟周期，不是真实硬件计时或编译器静态估算。', '',
        '| 形状 | 路径 | 模拟周期 | 指令数 | Profiling |',
        '|---|---|---:|---:|---|']
for record in records:
    archive = Path(record['archive'])
    data = json.loads((archive/'report/results/kernel_0_reports/summary.json').read_text())
    assert record['correct'] and 'SIMULATOR_CORRECT' in (archive/'npusim.log').read_text()
    assert data == record['profile']
    metrics = data['kernel_info']
    rows.append(f"| {'×'.join(map(str,record['shape']))} | {record['mode'].upper()} | {metrics['kernel_total_clocks']} | {metrics['kernel_instructions_executed']} | [报告]({archive}/report/index.html) |")
rows += ['', '## IR 对比', '',
         f'* [1D IR]({root}/256_device.tir.html) · [1D AscendC]({root}/256_kernel.asc.html)',
         f'* [2D IR]({root}/4x64_device.tir.html) · [2D AscendC]({root}/4x64_kernel.asc.html)', '',
         'SIMT 使用线程映射与 float2 运算；SIMD 使用掩码及 vld/vadd/vsts。每条路径保存 86 个 pass 快照。', '',
         '极小内核的模拟周期可能在不同运行间波动；这些单次结果用于调试流水与指令，不用于宣称真实硬件加速比。', '',
         '[环境说明](/workspace/setup/tilelang/README.md)']
(root/'SUMMARY.md').write_text('\n'.join(rows)+'\n')
print('\n'.join(rows[:12]))
