# Velvet46 ZMK 配置

这是 Velvet46 分体键盘的 ZMK 固件配置，基于 ZMK 0.4，并在此基础上保留现有键位、组合键、背光和 Nice!View 屏幕配置。

## 固件功能

- 左右两侧使用 nice!nano 控制器，通过 BLE split 连接。
- 左侧构建包含 `nice_view_custom` 屏幕；右侧构建包含 Nice!View 和 ZMK Studio 支持。
- 右侧固件启用 ZMK Studio、USB UART Studio RPC，以及 BLE 管理和设置 RPC；左右侧启用 split relay/settings RPC。
- Prospector dongle 模式使用 XIAO BLE / nRF52840 作为 USB split central，通过 BLE 连接左右键盘 peripheral，并显示 WALL-E / Codex 主题。
- GitHub Actions 同时构建原始左右侧固件，以及 dongle 模式的接收器、左右 peripheral 和 settings reset 固件，并将 UF2 文件作为 `firmware` artifact 上传。
- 按键布局和图示见 [键位图](keymap-drawer/velvet.svg)。

## 已移除的硬件功能

本配置不包含编码器、轨迹球或鼠标控制层。相关传感器、输入处理器及鼠标行为已从键盘设备树、键位图和配置中移除。

## 下载固件

推送代码后，或在仓库的 **Actions → Build ZMK firmware → Run workflow** 手动启动构建。构建完成后，在对应运行记录的 **Artifacts** 下载 `firmware`。压缩包根目录直接放置以构建目标命名的 `.uf2` 文件，无需进入子文件夹：

- `velvet_left.uf2`：左侧键盘
- `velvet_right.uf2`：右侧键盘
- `settings_reset.uf2`：清除 ZMK 保存的设置；仅在需要重置配对或存储设置时使用

每侧键盘应刷写对应的 UF2 文件。左右固件均使用 nice!nano 目标板。

Prospector dongle 模式需要刷写同一次 Actions 构建的以下三个固件：

- `velvet_prospector_dongle_walle.uf2`：XIAO Prospector 接收器，也是电脑的 USB 键盘设备。
- `velvet_left_dongle.uf2`：左手 peripheral。
- `velvet_right_dongle.uf2`：右手 peripheral。
- `settings_reset_xiao.uf2`：清除 Prospector 接收器保存的 BLE 配对。
- `settings_reset.uf2`：清除 nice!nano 键盘保存的 BLE 配对。

初次切换模式时，接收器和左右手应使用同一构建批次固件；分别刷写 `settings_reset_xiao` 与 `settings_reset` 清除新旧 central/peripheral 保存的配对，再将两手与 Prospector 重新配对。恢复普通键盘模式时，刷写原 `velvet_left` 与 `velvet_right` 固件。显示主题采用 Prospector 的 `prospector_theme_walle`，主题代码由 `zmk-prospector` 的 `prospector-themes` 模块提供。Dongle 模式不启用 DYA Studio 扩展、编码器、轨迹球或 scanner BLE observer。

## 本地构建

在安装 ZMK 所需的 west、Python 和 Zephyr 工具链后，从仓库根目录执行：

```sh
west init -l config
west update --narrow
west zephyr-export
west zmk-build -d ./build -q
```

构建目标定义在 [`build.yaml`](build.yaml)，West 依赖清单位于 [`config/west-dependency.yml`](config/west-dependency.yml)。
