# Velvet46 ZMK 配置

这是 Velvet46 分体键盘的 ZMK 0.4 固件配置，保留现有键位、组合键、背光、Nice!View 屏幕和 DYA Studio 支持。本分支新增 nice!nano K（nRF52833）作为 USB dongle 接收器：接收器担任 split central，通过 BLE 连接左右键盘；左右键盘担任 peripheral，并继续使用各自的 Nice!View 屏幕。

本分支的 dongle 使用无屏幕的 nice!nano K。接收器固件提供 USB 键盘连接与 ZMK Studio；Prospector 屏幕、触控和主题不属于此 dongle 配置。编码器和轨迹球相关功能已从键盘配置移除。

## GitHub Actions 固件

在 **Actions → Build ZMK firmware → Run workflow** 手动启动构建，或推送提交触发构建。完成后，在运行记录的 **Artifacts** 下载 `firmware`。压缩包根目录直接放置以固件名称命名的 UF2 文件，无需进入子文件夹：

- `velvet_nano_dongle.uf2`：nice!nano K（nRF52833）USB 接收器 / split central，默认使用板卡 2.0.0 修订版。
- `velvet_left_dongle.uf2`：dongle 模式下的左手 peripheral。
- `velvet_right_dongle.uf2`：dongle 模式下的右手 peripheral。
- `settings_reset_nano.uf2`：清除接收器保存的设置和 BLE 配对。
- `velvet_left.uf2`、`velvet_right.uf2`：标准左右手固件。
- `settings_reset.uf2`：清除 nice!nano 左右手保存的设置和 BLE 配对。

首次切换到 dongle 模式时，接收器和左右手应刷写同一次 Actions 构建生成的固件。按需先刷写 `settings_reset_nano.uf2` 和左右手的 `settings_reset.uf2` 清除旧配对，再将左右手与接收器配对。恢复标准 split 模式时，刷写 `velvet_left.uf2` 与 `velvet_right.uf2`。

## 本地构建

构建目标定义在 [`build.yaml`](build.yaml)，West 依赖清单位于 [`config/west-dependency.yml`](config/west-dependency.yml)。本分支在 `boards/nicekeyboards/nice_nano_k` 提供 nice!nano K 板卡定义，供 dongle 接收器和接收器配对重置固件使用。
