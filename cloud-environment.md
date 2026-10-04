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
