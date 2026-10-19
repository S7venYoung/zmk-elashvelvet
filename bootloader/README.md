# nRF52833 Nano Dongle Bootloader

原全量恢复镜像与新版 BL 更新均已获用户实机确认，二者所包含的修正不同。仅适用于本项目原 nRF52833 Nano K 小接收器，不用于 nice!nano nRF52840 或左右键盘。

## 新版 BL 更新文件

新版包含显示名 **Nano Dongle**、UF2 卷标 **NANO DONGLE**、独立短插拔，以及 USB 已挂载时取消 30 秒强制复位的修正。旧超时可中断 macOS Finder 复制，造成应用仅写入前半段；不是通过改变 VID 解决。

文件位置：[updates/nano-dongle-macos](updates/nano-dongle-macos/README.md)。

| 下载 | 方式 | 状态 |
|---|---|---|
| [BL-only HEX](updates/nano-dongle-macos/nano_dongle_BL_ONLY.hex) | SWD/J-Link 按 HEX 地址只更新 BL，不整片擦除 | 文件/地址检查与用户实机验证通过 |
| [两步 UF2 ZIP](updates/nano-dongle-macos/Nano_Dongle_UF2_Update.zip) | 兼容旧 BL 下按 01→02 更新 | 格式检查与用户实机验证通过；清除设置与配对 |
| [01 更新 BL](updates/nano-dongle-macos/01_nano_dongle_bootloader_update.uf2) / [02 恢复应用](updates/nano-dongle-macos/02_velvet_nano_dongle_restore.uf2) | ZIP 内原文件的单独下载 | 不得只用 01，不得同时拖入 |

两步 UF2 使用 0x63000–0x6CFFF 暂存区，覆盖部分应用和设置。02 用于恢复该更新包的旧应用和清理暂存，**不是最新猫咪套装应用**。详细操作及 SHA256 见上方目录 README、[校验文件](updates/nano-dongle-macos/SHA256SUMS) 和 [validation.json](updates/nano-dongle-macos/validation.json)。更新包原样附上，未重新构建，也未自动写入任何设备。

## 原已验证全量恢复镜像

[nano33_replug_FULL_RECOVERY.hex](firmware/nano33_replug_FULL_RECOVERY.hex)，SHA256：

`b766e68a42c30517b6f767162c40b975c190a696411103b9fc596f8ef50a6f42`

该文件与此前实测的 `nano33_replug_FULL_RECOVERY_TEST.hex` 内容一致，仅去掉文件名 TEST。2026-10-16 用户确认 UF2 磁盘/应用刷入、正常启动、两次短插拔后第三次进入 BL 均通过。完整 [validation.json](firmware/validation.json) 保持原样。

**此旧文件磁盘名为 NANO33TEST，仍含旧 USB 超时行为，不包含新版的超时修正与改名。**

J-Link/SWD 全量恢复：nRF52833_xxAA、SWD，建议从 100 kHz 连接；先备份 Flash/UICR，按 HEX 自带地址写入、校验、重新上电，不另填 0x1000 偏移。完整镜像会清除当前应用及设置，保留原模板的 MBR、SoftDevice 和 UICR 值并换入旧短插拔 BL；随后再刷对应的正常应用 UF2。

## 独立短插拔入口

前两次冷上电在约 2 秒内拔下，第三次保持连接进入 UF2；实际建议两次都不到 1 秒就拔下。正常持续上电约 2 秒后清零日志并启动应用。不依赖 ZMK、USB HID 或 DYA。拔下期间不能计时，软件/看门狗/复位引脚重启不增加计数。

普通 `velvet_nano_dongle.uf2` 不更新 BL。DYA 的 BL 请求属于应用入口；独立 BL 短插拔用于应用不能启动时恢复。

## 源码和分区

基础锁定 `kbladewht/Adafruit_nRF52_Bootloader` 的 `d7c55d99c97633a770c5536dc113e3849f3bc91e`。原文件带 dirty，无法据此完整还原未提交修改。本项目去掉 Feather 的 LED/NeoPixel/按钮并关闭 DC/DC，使用专用冷上电日志。

- 应用从 0x1000 开始，代码上限 0x64000。
- 冷上电日志页 0x65000–0x65FFF；ZMK 设置从 0x66000 开始。
- BL 0x74000–0x7DFFF；MBR 参数 0x7E000；BL 设置 0x7F000。
- [bootloader-test](../bootloader-test/) 含补丁、冷上电/日志模拟和 USB 超时测试。

BL 构建 workflow 仅手动触发。新版 BL-only 与两步 UF2 已由用户于 2026-10-19 确认实机验证通过（确认来源：本次对话）。本次没有触发 Actions。
