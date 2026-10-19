# Nano Dongle 新版 BL 附件（候选）

仅用于本项目原来的 nRF52833 Nano K 小接收器。BL 名称 Nano Dongle，UF2 磁盘 NANO DONGLE；含独立短插拔和 USB 挂载后不强制触发 30 秒超时复位的修正。以下文件均为此前已构建文件的原样附件，**未重新编译、未实机验证**。

## 两步 UF2 更新

[下载 ZIP](Nano_Dongle_UF2_Update.zip)，或分别下载 [01](01_nano_dongle_bootloader_update.uf2) 与 [02](02_velvet_nano_dongle_restore.uf2)。两者必须配套，不能同时拖入。只用于旧 BL 与本项目板身份和分区兼容的接收器，保留 J-Link 恢复手段。

1. 用两次“插入不到 1 秒拔下”、第三次保持连接进入旧 NANO33TEST。
2. 只拖入 `01_nano_dongle_bootloader_update.uf2`。等复制及更新完成，期间不要拔出。
3. 更新完成后重新插入，应进入名为 NANO DONGLE 的恢复磁盘。此时 BL 发现暂存残留，等待第二步。
4. 只拖入 `02_velvet_nano_dongle_restore.uf2`，等待完成，重新配对并检查 USB、DYA 和输入。
5. **02 包含配套的旧接收器应用，只用于恢复暂存区；不是最新猫咪套装固件**。需要目标版本时，再刷入同批正常接收器、左手和右手应用。普通应用更新以后不用重复这两步。

这不是普通应用 UF2。暂存范围 0x63000–0x6CFFF 覆盖部分应用末尾、日志和设置；第二步恢复应用并清理受影响区域，**会清除设置和蓝牙配对**。缺少第二步可能导致不能正常启动。第一步是 BL 专用 family 0xD663823C，第二步是 nRF52833 应用 family 0x621E937A；它们不是 nRF52840 固件。

不要使用通用 BL 自更新 UF2 替代本专用包，也不要把本包用于不同板子、不同分区或左右键盘。此包没有物理写入实测，步骤描述不能视为成功保证。

## J-Link 的 BL-only 更新

[nano_dongle_BL_ONLY.hex](nano_dongle_BL_ONLY.hex) 只含 0x74000–0x7DFFF 的 BL 数据，不是完整恢复镜像，不含 MBR、SoftDevice、UICR 或正常应用。

确认目标为 nRF52833，先备份 Flash/UICR。使用 SWD、低速连接，按 HEX 自带地址写入并校验；**不要做整片 erase/recover，不要填入 0x1000 偏移**。保留 MBR/UICR/应用/设置。旧损坏或错误 UICR/MBR 不能靠这个 BL-only 文件恢复，需另用全量恢复方案。

## 验证记录与校验

[validation.json](validation.json) 保留硬件状态 false、原 BL 源提交、UF2 family、暂存区和原文件 SHA256。已重新核对 HEX 行校验和、BL 地址范围/名称、UF2 magic/family/块序号/范围、第一步 BL 内容与 HEX 一致，以及第二步日志/设置区清理。

[SHA256SUMS](SHA256SUMS) 覆盖 BL-only、两份 UF2 和 ZIP。它只能证明文件内容一致，不证明硬件兼容或刷入成功。
