# Velvet46 ZMK 配置

这是 Velvet46 的 ZMK 0.4 / Zephyr 4.1 配置，保留左右键盘各自的 Nice!View，并支持两种 USB dongle：Prospector dongle 分支由 XIAO Prospector 担任 BLE split central；标准模式仍构建左右手键盘。Prospector 使用 WALL-E / Codex 主题。

DYA Studio 模块包括 BLE 管理、Custom Settings、Fast Keymap、Device Info、Watchdog、Runtime Macro 和 Runtime Combo。Dongle 模式 central 运行 Studio，左右手作为 BLE peripheral 并 relay 设置。键盘不包含编码器、轨迹球或鼠标控制功能。

## Actions 固件

Actions artifact `firmware` 内直接平铺命名 UF2 文件：

- `velvet_prospector_dongle_walle.uf2`：Prospector USB 接收器 / split central
- `velvet_left_dongle.uf2`、`velvet_right_dongle.uf2`：dongle 模式左右手 peripheral
- `settings_reset_xiao.uf2`：清除接收器设置和配对
- `velvet_left.uf2`、`velvet_right.uf2`：普通 split 左右手固件
- `settings_reset.uf2`：清除 nice!nano 键盘设置和配对

Dongle 模式三块设备应刷写同一次 Actions 生成的固件。清除旧配对时，接收器使用 `settings_reset_xiao.uf2`，左右手使用 `settings_reset.uf2`。DYA Studio 通过 USB 连接 central，在 Chromium 浏览器打开 <https://studio.dya.cormoran.works/>。

## Prospector 彩屏与内存配置

接收器使用 WALLE 自定义屏幕和 RGB565（16 位）彩色绘图。240×280 屏幕采用两个各占整屏 10% 的绘图缓冲，总计 26,880 字节，通过分块刷新保留完整分辨率与颜色；LVGL 界面内存池为 49,152 字节，显示线程栈为 8,192 字节。不要把单色 Nice!View 的缓冲配置直接用于接收器。

`build.yaml` 显式覆盖 `config/velvet.conf` 的通用设置，接收器行为队列为 64，BLE ACL/事件/L2CAP 发送缓冲数量分别为 3/6/4。DYA 模块保持启用，USB RPC 使用 `studio-rpc-usb-uart` snippet。Actions 会打印最终配置与 RAM 分配，便于检查覆盖是否生效。
