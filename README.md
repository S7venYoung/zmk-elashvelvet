# Velvet46 ZMK 配置

这是 Velvet46 分体键盘的 ZMK 0.4 / Zephyr 4.1 配置。左右手使用 Nice!View，通过 BLE split 连接；右手 central 提供 USB 和 DYA Studio，左手作为 peripheral 转发设置。

DYA Studio 模块包括 BLE 管理、持久化自定义设置、运行时宏和组合键、Fast Keymap、设备信息及 watchdog 诊断。键盘固件不包含编码器、轨迹球或鼠标控制功能。此分支还附带独立的 Prospector scanner 构建：右手广播键盘状态，XIAO BLE scanner 使用触控和 Codex 配额仪表主题。

## 构建和下载

- **Build ZMK firmware**：构建左右键盘和 `settings_reset`，Actions artifact `firmware` 中的 UF2 文件直接平铺。
- **Build Prospector scanner**：单独构建 scanner 固件，使用 Codex2 主题。

DYA Studio 通过 USB 连接右手键盘，在 Chromium 打开 <https://studio.dya.cormoran.works/>。构建矩阵见 [`build.yaml`](build.yaml)，DYA/ZMK/Zephyr 依赖见 [`config/west-dependency.yml`](config/west-dependency.yml)。
