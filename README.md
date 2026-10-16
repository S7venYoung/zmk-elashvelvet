# nRF52833 Bootloader 测试

这是隔离的 Bootloader 测试分支，不改动 Nano/Fight 应用分支。来源锁定 kbladewht/Adafruit_nRF52_Bootloader 的 d7c55d99c97633a770c5536dc113e3849f3bc91e，与原 HEX 内嵌提交一致；原 HEX 标注 dirty，作者未提交的修改不能由公开源码完整还原。

Actions 构建 baseline（原源码）和 replug（无按键接收器短插拔候选），并测试状态判定与 HEX 地址。产物仅含 0x74000 起始的 BL 区，不含 MBR、SoftDevice、应用、UICR 或配对设置。禁止作为普通应用 UF2 刷入。

replug 在每次冷上电时，在独立 Flash 页 0x65000-0x65fff 记录阶段；该页位于当前 Velvet 应用结束 0x64000 与设置开始 0x66000 之间的空隙，必须保持专用且初次为空白。无按键硬件不使用 Feather 的 LED/NeoPixel/按钮 GPIO。

操作：前两次上电后在约 2 秒内拔下，第三次进入 UF2（NANO33TEST）。普通上电等待约 2 秒后清零计数再启动应用；逻辑在 BL 中执行，即使应用卡死也不依赖应用清零。软件/看门狗/复位引脚重启不计为插拔；断电期间没有计时能力。追加式日志减少擦除次数，页满才擦除；遇到外来/损坏日志只进入 DFU，不自动擦除陌生数据。

静态测试不能确认真实电路和启动器行为。上机前用 J-Link 保存全 Flash/UICR 和原始 HEX；核对 UICR BL=0x74000、MBR参数=0x7e000、日志页空白。只对 BL 所在扇区写入和校验，不全片擦除，不修改 UICR。首次写入需要 SWD/J-Link。测试产物尚未通过实机 USB、冷上电和掉电中断测试，不应当作稳定版。
