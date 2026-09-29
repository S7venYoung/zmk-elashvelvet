# Velvet46 ZMK 配置

这是 Velvet46 分体键盘的 ZMK 0.4 / Zephyr 4.1 固件配置。左右键盘通过 BLE split 连接，并各自使用 Nice!View 屏幕。普通模式下右手为 split central，左手为 peripheral。

右手 central 启用 DYA Studio 扩展：BLE 管理、持久化自定义设置、运行时宏与组合键、Fast Keymap、设备信息和 watchdog 诊断。左手 peripheral 提供设置存储和 split relay，使 central 上的 Studio 能访问左右两侧。固件不包含编码器、轨迹球或鼠标控制功能。

## 下载固件

在 **Actions → Build ZMK firmware → Run workflow** 启动构建。完成后在运行记录的 **Artifacts** 下载 `firmware`；压缩包内是根目录平铺的 `.uf2` 文件：

- `velvet_left.uf2`：左手键盘 peripheral
- `velvet_right.uf2`：右手键盘 central，启用 USB Studio RPC 和 DYA Studio 功能
- `settings_reset.uf2`：清除键盘保存的设置和 BLE 配对

刷写固件后，将键盘通过 USB 连接电脑，并使用 Chromium 浏览器打开 <https://studio.dya.cormoran.works/> 连接 DYA Studio。

构建目标定义在 [`build.yaml`](build.yaml)，依赖及 ZMK/Zephyr 版本定义在 [`config/west-dependency.yml`](config/west-dependency.yml)。
