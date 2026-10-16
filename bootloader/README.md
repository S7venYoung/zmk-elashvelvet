# nRF52833 Nano Dongle 独立 Bootloader

2026-10-16 用户确认全量恢复镜像已通过实机测试：UF2 磁盘和刷入、正常启动、两次短插拔后第三次进入 BL。该记录仅针对下面固定 SHA256 的文件，不代表每次重新编译的文件都已上板验证。

## 已验证全量恢复镜像

下载 [nano33_replug_FULL_RECOVERY.hex](firmware/nano33_replug_FULL_RECOVERY.hex)，SHA256：

`b766e68a42c30517b6f767162c40b975c190a696411103b9fc596f8ef50a6f42`

此文件与先前实机验证的 nano33_replug_FULL_RECOVERY_TEST.hex 内容相同，只改了文件名。完整记录见 [validation.json](firmware/validation.json)。

J-Link/SWD 首次安装：nRF52833_xxAA、SWD、100 kHz；先保存 Flash/UICR 备份，再按 HEX 自带地址完整恢复、校验和重新上电，不填写 0x1000 偏移。此完整镜像清除当前 ZMK 应用、配对和设置，保留原始 HEX 的 MBR、SoftDevice 和 UICR 值，并换入短插拔 BL。恢复后应出现 NANO33TEST，随后将 nRF52833 应用 UF2 复制进去。

日常只刷 velvet_nano_dongle.uf2 即可，不需要重刷 BL；这不是 nRF52840/左右手的启动器。

## 不依赖应用的短插拔

前两次冷上电都在约 2 秒内拔下，第三次插入进入 UF2；正常连续上电等待约 2 秒后，BL 清零计数再启动应用。检测在 BL 内执行，不需要 ZMK、USB HID 或 DYA 正常工作。软件、看门狗、复位引脚重启不会增加计数，拔下期间无法计时。

此入口与 ZMK 应用中的旧 1.2 秒延迟/10 秒插拔窗口是两套机制；安装本 BL 后，救砖使用本节的“2 秒内拔下”方式。应用里的 DYA/Studio 进入 BL 入口仍可用。

## 源码、分区及构建

基础锁定 kbladewht/Adafruit_nRF52_Bootloader 的 d7c55d99c97633a770c5536dc113e3849f3bc91e，与原始 HEX 的提交标识相同。原文件带 dirty，未提交改动无法完整还原。本方案移除 Feather 的 LED/NeoPixel/按钮使用并关闭 DC/DC，适配无按键接收器。

[bootloader-test](../bootloader-test/) 保存补丁、状态判断和断电模拟测试。日志页为 0x65000–0x65FFF，必须专用；应用代码不超过 0x64000，ZMK 设置始于 0x66000；BL 从 0x74000 开始，MBR 参数在 0x7E000，BL 设置在 0x7F000。追加式日志减少擦除次数，未知或损坏记录进入 DFU，不擦除外来数据。

Actions 的 Test nRF52833 Bootloader 同时构建原始 baseline 和 replug 候选，测试两次断电、第三次进入、正常清零、看门狗、页满整理、外来数据保护及地址范围。nano33-full-recovery-verified artifact 提供固定的实机验证镜像；另两个 TEST-ONLY artifact 是重新构建的 BL-only 候选，只含 BL 区，不是全量恢复文件，不含应用/MBR/SoftDevice/UICR。测试模拟不能覆盖所有物理掉电瞬态。
