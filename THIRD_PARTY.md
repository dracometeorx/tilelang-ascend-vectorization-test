# 第三方来源

- TileLang 主仓库：https://github.com/dracometeorx/tilelang ，固定提交见 `versions.json`。安装时克隆；不复制主仓库源代码。
- NPU-IR 前端 wheel：https://github.com/tile-ai/tilelang-ascend/releases/tag/v0.1.1.030-pre-release 。安装器固定下载 URL 和 SHA256，使用独立虚拟环境。
- PTOAS VMI：https://github.com/hw-native-sys/PTOAS/releases/tag/vmi-v0.1.9 。安装器固定下载 URL 和 SHA256。
- CANN 9.2.0 beta.2：用户指定的华为 CANN RPM 源 `https://repo.oepkgs.net/ascend/cann/`，保留 RPM 签名和内层归档 SHA256 检查。SDK、模拟器、PTO ISA/NPU-IR 编译器及其许可随安装包提供，不在本仓库再分发。
- Debian sysroot 包：来源、版本、SHA256 见 `sysroot-packages.json`。包不在 Git 中；其校验值来自原环境验证过签名的 Debian bookworm 软件包索引。
- NPU-IR 测试依据上游 `examples/elementwise/example_elementwise_add.py` 的 TileLang API 编写；模拟入口参考厂商 runtime API。`examples/ir/` 是这些小型加法实际生成的文本，不包含厂商编译器二进制。

使用、下载和再分发第三方组件应遵守各自附带许可。此仓库没有为第三方软件授予新的许可，也没有把它们重新许可为测试脚本的许可。
