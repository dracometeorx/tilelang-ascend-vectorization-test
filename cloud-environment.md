# 云环境配置示例

工作目录可改为任意无空格的绝对路径。以下假定本仓库挂载到 `/workspace/tilelang-ascend-vectorization-test`，独立实验工作目录为 `/workspace/a5-lab`。

## install_script

```bash
#!/usr/bin/env bash
set -euo pipefail
cd /workspace/tilelang-ascend-vectorization-test
python3 bootstrap.py --workspace /workspace/a5-lab --install
```

系统依赖和 uv 必须先按 README 准备。首次原生编译可能需要较长时间；不要把已有构建缓存误认为干净机器安装验证。

## start_skill

使用现有 checkout；云任务已经隔离，不创建额外 worktree。保留用户改动。

该实验不需要后台服务。发布快照需要保留 `/workspace/a5-lab` 内的 checkout、构建目录、Python 环境、SDK、脚本和缓存。不要假定进程会随快照恢复。

主环境：

```bash
source /workspace/a5-lab/setup/backends/activate.sh
ptoas --version
bishengir-compile --version
```

运行 `bash /workspace/a5-lab/setup/tilelang/run.sh` 或 `bash /workspace/a5-lab/setup/backends/run.sh`。NPU-IR 前端应由脚本在独立 Python 3.11 环境运行，避免覆盖主 Python 3.12 环境。

阅读 `README.md` 的兼容边界；同时检查数值日志和模拟报告。保存配置、安装、执行与发布快照是不同步骤。

## 网络

根据平台现有配置保留必要域名；不要用此清单覆盖未知的已有列表。安装使用 GitHub 及其 release 下载域、PyPI/package-manager 域、`download.pytorch.org`、`repo.oepkgs.net`、`deb.debian.org`。没有运行时密钥需求；GitHub 凭据只用于访问用户选择的私有代码仓库，不应写入本仓库。

新版 `tile-ai/tilelang-mlir-ascend@013dbbf5` 的 A5 构建还需要 `gitcode.com` 上固定的 `Ascend/AscendNPU-IR-Dev@77f5b061` 及其完整 MLIR 开发依赖。允许域名不等于拥有仓库访问权限：2026-10-06 新任务已确认策略生效，但该仓库匿名 Git 请求返回 401，认证后仍返回 `can not read project`。后续实测发现官方公开 `Ascend/AscendNPU-IR` 可直接 fetch 相同固定提交 `77f5b061`，可仅在本地配置覆盖子模块 URL，保持源码 gitlink 不变。需要凭据时应通过环境安全配置传入，不写入源码、日志、URL 或 shell 配置。不要关闭 TLS 校验或绕过代理。

同次恢复发现快照只含旧测试仓库 `840972e`，没有后续场景脚本、完整结果和新版虚拟环境。必须先 fetch 核对远端，再检查实际文件；旧 tar/bundle、已有目录或文档内的成功数字不能证明迁移完整或本次运行成功。参见[本次恢复证据](examples/scenarios/npuir-main-013dbbf5/preflight.json)。
