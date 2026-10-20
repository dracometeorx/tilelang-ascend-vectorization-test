"""跑一遍 T.Parallel 向量化工作负载矩阵，保存中间 IR 并判定结果。

用法（在 tilelang-mlir-ascend 仓库根目录，或任何 PYTHONPATH 已配好的地方）：

    python3 run_matrix.py --out-dir /path/to/artifacts

    # 只跑一个用例并把 IR 打到屏幕
    python3 run_matrix.py --out-dir /tmp/a --only binary_add --verbose

    # 顺带走完整 lower 拿 MLIR（需要能跑 codegen）
    python3 run_matrix.py --out-dir /path/to/artifacts --mlir

每个用例在**独立子进程**里跑：预期会触发 C++ ICHECK 的用例（如
reduction_plus_equal）会使进程 abort，子进程隔离保证其余用例照常完成。

产物与判定规则见同目录 README.md。本脚本在研究主机上只做过语法检查，
未执行过编译器。
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

STAGES = ("00-frontend.tir", "01-before-vectorize.tir", "02-after-vectorize.tir")


# ==========================================================================
# 子进程：单个用例
# ==========================================================================


def classify(mod):
    """从 NpuLoopVectorize 之后的 IRModule 里提取结构事实并给出判定。"""
    from tilelang import tvm
    from tvm import tir

    facts = {
        "parallel_loops": [],
        "serial_loops": [],
        "npuir_calls": [],
        "scalar_stores": 0,
        "region_max_size": 0,
    }

    def visit(node):
        if isinstance(node, tir.For):
            extent = str(node.extent)
            if node.kind == tir.ForKind.PARALLEL:
                facts["parallel_loops"].append(extent)
            else:
                facts["serial_loops"].append(extent)
        elif isinstance(node, tir.BufferStore):
            facts["scalar_stores"] += 1
        elif isinstance(node, tir.Call):
            op_name = getattr(node.op, "name", "")
            if op_name.startswith("tl.") and op_name != "tl.region":
                sizes = []
                regions = []
                for arg in node.args:
                    if (
                        isinstance(arg, tir.Call)
                        and getattr(arg.op, "name", "") == "tl.region"
                    ):
                        # tl.region(BufferLoad(buf, offsets...), access_mask, size...)
                        load = arg.args[0]
                        local_sizes = []
                        for s in arg.args[2:]:
                            try:
                                local_sizes.append(int(s))
                            except (TypeError, ValueError):
                                local_sizes.append(-1)  # 动态
                        sizes.extend(local_sizes)
                        access = None
                        try:
                            access = int(arg.args[1])
                        except (TypeError, ValueError):
                            pass
                        regions.append(
                            {
                                "buffer": str(getattr(load, "buffer", "?").name)
                                if hasattr(load, "buffer")
                                else "?",
                                # offset 对测对齐/偏移是关键信息，保留原样文本
                                "offsets": [str(i) for i in getattr(load, "indices", [])],
                                "access": {1: "r", 2: "w"}.get(access, access),
                                "sizes": local_sizes,
                            }
                        )
                facts["npuir_calls"].append(
                    {"op": op_name, "region_sizes": sizes, "regions": regions}
                )
                if sizes:
                    facts["region_max_size"] = max(
                        facts["region_max_size"], max(sizes)
                    )

    for gv, func in mod.functions.items():
        tir.stmt_functor.post_order_visit(func.body, visit)

    # 判定不能只数全函数里的 tl.* 调用：用例自己写的 T.copy(A, a) 这类搬运语句
    # 也是 tl.copy，会被误当成向量化证据。真正的信号是**残留的 parallel 循环
    # 里还有没有标量 BufferStore**——有就说明那条语句没被向量化。
    parallel_fors = []
    for gv, func in mod.functions.items():

        def collect(node):
            if isinstance(node, tir.For) and node.kind == tir.ForKind.PARALLEL:
                parallel_fors.append(node)

        tir.stmt_functor.post_order_visit(func.body, collect)

    def scan_subtree(stmt):
        """统计某个子树里的标量 store 与向量算子（含 region 最大长度）。"""
        acc = {"stores": 0, "vec_ops": 0, "max_size": 0}

        def v(node):
            if isinstance(node, tir.BufferStore):
                acc["stores"] += 1
            elif isinstance(node, tir.Call):
                name = getattr(node.op, "name", "")
                if name.startswith("tl.") and name != "tl.region":
                    acc["vec_ops"] += 1
                    for arg in node.args:
                        if (
                            isinstance(arg, tir.Call)
                            and getattr(arg.op, "name", "") == "tl.region"
                        ):
                            for s in arg.args[2:]:
                                try:
                                    acc["max_size"] = max(acc["max_size"], int(s))
                                except (TypeError, ValueError):
                                    pass

        tir.stmt_functor.post_order_visit(stmt, v)
        return acc

    inside = {"stores": 0, "vec_ops": 0, "max_size": 0}
    for f in parallel_fors:
        a = scan_subtree(f.body)
        inside["stores"] += a["stores"]
        inside["vec_ops"] += a["vec_ops"]
        inside["max_size"] = max(inside["max_size"], a["max_size"])
    facts["inside_parallel"] = inside

    n_vec_total = len(facts["npuir_calls"])
    if not parallel_fors:
        # parallel 循环全部消去
        verdict = "full" if n_vec_total else "scalar"
    elif inside["stores"] and inside["vec_ops"]:
        verdict = "mixed"
    elif inside["stores"]:
        # 循环里还是标量读写：这条语句没被向量化
        verdict = "scalar"
    elif inside["vec_ops"] and inside["max_size"] <= 1:
        # 拆解成功但合并失败，残留单元素 region：Q3 §4 / Q6 §4 的危险形态
        verdict = "unmerged"
    elif inside["vec_ops"]:
        verdict = "partial"
    else:
        verdict = "scalar"
    facts["verdict"] = verdict
    return facts


def run_one(name, out_dir, mode, want_mlir, verbose):
    os.environ["TILELANG_ASCEND_MODE"] = mode
    import tilelang  # noqa: F401  (导入顺序：先设环境变量)
    from tilelang import tvm
    from tilelang.engine.phase import LowerAndLegalize
    import tilelang.transform

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import cases

    if name not in cases.BY_NAME:
        raise SystemExit(f"unknown case: {name}")
    category, builder, expected, ref = cases.BY_NAME[name]

    case_dir = out_dir / name
    case_dir.mkdir(parents=True, exist_ok=True)

    func = builder()
    mod = tvm.IRModule({"main": func})
    (case_dir / STAGES[0]).write_text(mod.script(), encoding="utf-8")

    target = tvm.target.Target("npuir")
    before = LowerAndLegalize(mod, target)
    (case_dir / STAGES[1]).write_text(before.script(), encoding="utf-8")

    after = tilelang.transform.NpuLoopVectorize()(before)
    after_text = after.script()
    (case_dir / STAGES[2]).write_text(after_text, encoding="utf-8")

    facts = classify(after)
    result = {
        "case": name,
        "category": category,
        "expected": expected,
        "reference": ref,
        "mode": mode,
        "tilelang": str(Path(tilelang.__file__).resolve()),
        **facts,
    }
    result["match"] = facts["verdict"] == expected
    note = getattr(cases, "NOTES", {}).get(name)
    if note:
        result["manual_check"] = note

    if want_mlir:
        from tilelang.engine.lower import lower

        try:
            mlir = lower(func, target="npuir")
            if isinstance(mlir, str):
                (case_dir / "03-codegen.mlir").write_text(mlir, encoding="utf-8")
                result["mlir"] = "ok"
            else:
                result["mlir"] = f"unexpected type {type(mlir).__name__}"
        except Exception as exc:  # noqa: BLE001
            result["mlir"] = f"{type(exc).__name__}: {exc}"
            (case_dir / "03-codegen.error.txt").write_text(
                f"{type(exc).__name__}: {exc}\n", encoding="utf-8"
            )

    (case_dir / "verdict.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    if verbose:
        print(after_text)
    print(json.dumps({k: result[k] for k in ("case", "verdict", "expected", "match")}))
    return result


# ==========================================================================
# 父进程：遍历 + 汇总
# ==========================================================================


def run_all(out_dir, mode, want_mlir, only, timeout):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import cases

    selected = [c for c in cases.CASES if not only or c[0] in only]
    rows = []
    for name, category, _fn, expected, ref in selected:
        cmd = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--out-dir",
            str(out_dir),
            "--case",
            name,
            "--mode",
            mode,
        ]
        if want_mlir:
            cmd.append("--mlir")
        print(f"[run] {name} ... ", end="", flush=True)
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
        except subprocess.TimeoutExpired:
            rows.append(
                dict(
                    case=name,
                    category=category,
                    expected=expected,
                    reference=ref,
                    verdict="timeout",
                    match=False,
                )
            )
            print("timeout")
            continue

        case_dir = out_dir / name
        case_dir.mkdir(parents=True, exist_ok=True)
        (case_dir / "stdout.txt").write_text(proc.stdout, encoding="utf-8")
        (case_dir / "stderr.txt").write_text(proc.stderr, encoding="utf-8")

        vfile = case_dir / "verdict.json"
        if proc.returncode == 0 and vfile.exists():
            row = json.loads(vfile.read_text(encoding="utf-8"))
        else:
            # 非零退出：可能是 Python 异常，也可能是 C++ ICHECK abort
            row = dict(
                case=name,
                category=category,
                expected=expected,
                reference=ref,
                verdict="error",
                returncode=proc.returncode,
                tail=proc.stderr.strip().splitlines()[-3:],
            )
            row["match"] = expected == "error"
        rows.append(row)
        print(f"{row['verdict']}{'' if row.get('match') else '  <== 与预期不符'}")

    (out_dir / "matrix.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_report(out_dir, rows, mode)
    bad = [r for r in rows if not r.get("match")]
    print(f"\n{len(rows)} 个用例，{len(bad)} 个与预期不符")
    for r in bad:
        print(f"  - {r['case']}: 预期 {r['expected']}，实际 {r['verdict']}")
    print(f"报告：{(out_dir / 'matrix.md').resolve()}")
    return 0 if not bad else 1


def write_report(out_dir, rows, mode):
    lines = [
        "# T.Parallel 向量化支持矩阵（实测）",
        "",
        f"模式：{mode}　用例数：{len(rows)}",
        "",
        "判定规则见 README.md。`unmerged` 表示生成了向量算子但 region 长度仍为 1，",
        "属于需要追查的形态。",
        "",
        "注意：\"全部算子\"列把用例自己写的 `T.copy` 搬运语句也算进来了，不能据此判断",
        "是否向量化。判定看的是\"parallel 内\"两列——残留循环里还有标量 store 就说明",
        "那条语句没被向量化。",
        "",
        "| 用例 | 类别 | 预期 | 实际 | 一致 | 保留的 parallel 轴 | parallel 内标量 store | parallel 内向量算子 | 全部算子 | 参考 |",
        "|---|---|---|---|---|---|---:|---:|---|---|",
    ]
    for r in rows:
        ops = ", ".join(
            sorted({c["op"].replace("tl.npuir_", "").replace("tl.", "") for c in r.get("npuir_calls", [])})
        )
        par = ", ".join(r.get("parallel_loops", [])) or "—"
        mark = "✓" if r.get("match") else "**✗**"
        ip = r.get("inside_parallel", {})
        lines.append(
            f"| `{r['case']}` | {r.get('category','')} | {r['expected']} | "
            f"{r['verdict']} | {mark} | {par} | {ip.get('stores','—')} | "
            f"{ip.get('vec_ops','—')} | {ops or '—'} | {r.get('reference','')} |"
        )
    lines += ["", "## 与预期不符的用例", ""]
    bad = [r for r in rows if not r.get("match")]
    if not bad:
        lines.append("无。")
    for r in bad:
        lines.append(
            f"- **{r['case']}**：预期 `{r['expected']}`，实际 `{r['verdict']}`。"
            f"检查 `{r['case']}/02-after-vectorize.tir` 与 `stderr.txt`。"
        )

    # verdict 判定不了的，列出来提醒人工看
    manual = [r for r in rows if r.get("manual_check")]
    if manual:
        lines += ["", "## 需要人工确认的用例", ""]
        lines.append("verdict 只看结构，下面这些还要看 `verdict.json` 的 `regions` 字段：")
        lines.append("")
        for r in manual:
            lines.append(f"- **{r['case']}**：{r['manual_check']}")

    # 把各用例的 region offset/长度摊平，方便直接扫
    lines += ["", "## region 明细（offset 与长度）", ""]
    lines.append("| 用例 | 算子 | buffer | 读写 | offset | 长度 |")
    lines.append("|---|---|---|---|---|---|")
    for r in rows:
        for call in r.get("npuir_calls", []):
            short = call["op"].replace("tl.npuir_", "").replace("tl.", "")
            for reg in call.get("regions", []):
                lines.append(
                    f"| `{r['case']}` | {short} | `{reg['buffer']}` | {reg['access']} | "
                    f"{', '.join(reg['offsets']) or '—'} | "
                    f"{', '.join(str(s) for s in reg['sizes']) or '—'} |"
                )
    lines.append("")
    (out_dir / "matrix.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--case", help="内部使用：在子进程里跑单个用例")
    p.add_argument("--only", nargs="*", default=None, help="只跑这些用例")
    p.add_argument("--mode", default="Developer", choices=["Developer", "Expert"])
    p.add_argument("--mlir", action="store_true", help="额外走完整 lower 保存 MLIR")
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--verbose", action="store_true")
    a = p.parse_args()

    a.out_dir.mkdir(parents=True, exist_ok=True)
    if a.case:
        run_one(a.case, a.out_dir, a.mode, a.mlir, a.verbose)
        return 0
    return run_all(a.out_dir, a.mode, a.mlir, a.only, a.timeout)


if __name__ == "__main__":
    sys.exit(main())
