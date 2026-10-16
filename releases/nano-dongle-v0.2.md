## Nano Dongle v0.2

适用分支：`codex/nano-dongle`。接收器为 **nice_nano_k / nRF52833 无屏小接收器**，左右手为配套 nice!nano 键盘。不要把接收器固件刷到 nRF52840 或 Fight OLED 接收器。

### 更新
- 保留 ZMK 0.4 / Zephyr 4.1、DYA USB 配置、进入 Bootloader 和配对管理功能。
- 修复 Zephyr 广播选项的枚举判断，完整广播名称 **Velvet46**，适配 Cube 的精确名称过滤。
- 单广播实例交替发送 Prospector 标准状态包和 Fight/Cube 状态包；扫描仪读取总 WPM，Cube 读取左右手独立 WPM。
- 左右手通过 split relay 分别上报电量和 WPM，以物理左右手标识区分，避免连接顺序造成错位。
- 修正右手 nice!view peripheral 显示配置。
- 设置清除固件增加清除完成后返回 Bootloader 的逻辑。

### 附件与刷写
| 文件 | 用途 |
| --- | --- |
| velvet_nano_dongle.uf2 | nRF52833 无屏接收器 |
| velvet_left_dongle.uf2 | 左手 |
| velvet_right_dongle.uf2 | 右手 |
| settings_reset_nano.uf2 | nRF52833 接收器设置/配对清除 |
| settings_reset.uf2 | nice!nano 键盘设置/配对清除 |
| SHA256SUMS.txt | 附件校验值 |

正常更新只需刷对应工作固件，**不要先刷 settings_reset**。已使用前一批左右手遥测固件的设备，此次只需更新接收器。重置固件仅在确需清除设置和配对时使用，之后重新刷工作固件；它不是 DYA 工作固件。

本 Release 为应用 UF2，**不更新 Bootloader**。应用无法运行时的短插拔恢复依赖此前单独安装的兼容 Bootloader；仅刷本 Release 不会增加 BL 内的恢复功能。

### 构建与验证
所有 UF2 来自 [GitHub Actions 38867621289](https://github.com/S7venYoung/zmk-elashvelvet/actions/runs/38867621289)，构建提交 `82376a87a4a49adacb29b11760605d37123c7bca`，未在本机编译。

实机已确认接收器 USB、扫描仪和 Cube 正常。实际广播名称为 `Velvet46`；抓包同时收到 ABCD 标准包和 ABCE Cube 包，包含左右电量、总 WPM 和左右独立 WPM。右手显示配置和 reset 返回 BL 已通过构建检查；本次未单独重新确认其硬件行为。
