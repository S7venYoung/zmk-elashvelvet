# Velvet46 · Nano Dongle

ZMK 0.4 / Zephyr 4.1，面向无屏 nRF52833 Nano K 接收器和左右 nice!nano nRF52840 键盘，两手各有 nice!view 屏幕。接收器通过 USB 连接电脑，通过 BLE split 连接左右键盘；不包含编码器、轨迹球或鼠标配置。

**本文更新范围截至双手猫咪主题套装**，包括 BL 更新、DYA、扫描仪/Cube 遥测、宏队列和猫咪显示。上述功能均已通过用户实机验证（用户于 2026-10-19 在本次对话确认）。本次仅同步文档与验证记录，没有触发 Actions、重编固件或向设备刷写。

## 固件与硬件对应

同一次 Actions 的 `firmware` 压缩包内，UF2 直接平铺，不使用固件名文件夹：

| 文件 | 用途 |
|---|---|
| `velvet_nano_dongle.uf2` | 原 nRF52833 Nano K 无屏接收器 |
| `velvet_left_dongle.uf2` | 左手 nice!nano nRF52840，dongle peripheral |
| `velvet_right_dongle.uf2` | 右手 nice!nano nRF52840，dongle peripheral |
| `settings_reset_nano.uf2` | 临时清除接收器设置与配对，完成后自动进入 BL |
| `settings_reset.uf2` | 临时清除 nice!nano 键盘设置与配对，完成后自动进入 BL |

接收器与左右手使用同批固件。nRF52833 和 nRF52840 的应用 UF2、BL、reset 文件不能混用。reset 固件不提供 DYA，刷完后应拖入正常固件；普通更新不用先刷 reset，也不必更新 BL。

Actions 仅允许手动触发；必须由用户确认后再构建。双手猫咪套装已由用户确认实机通过；**本次 BL 附件不包含新编译的双手猫咪应用固件**。

## 双手猫咪主题

左右手使用同一套原猫咪素材，各自显示：自身实时电量、与接收器的 BLE 连接状态、接收器回传的当前层号。内部层 0 显示 **LAYER 1**；数据未知或层状态过期时显示 `--`，不把未知电量当成 0%。连接指示点表示 split 连接，不代表电脑的蓝牙 profile 或实际 RSSI。

在 DYA Custom Settings 中选择接收器本地 `velvet_display`，将 `theme_set` 设置为 **0** 并使用 Persist 保存，即选择**左右都是猫咪**；默认也是 0。不分别设置左右主题。需配套更新接收器和两手固件，保存设置后退出 DYA，便于其他同步软件连接同一 USB CDC 端口。

主题独立目录：[src/display/themes/cat](src/display/themes/cat/README.md)。素材和渲染逻辑保留，共用显示管理器一次只绘制一套主题，不为每套主题额外创建 LVGL 屏幕或独立帧缓冲。

### 屏幕配置与此前白屏

保留原板 `CONFIG_ZMK_BACKLIGHT=y`、开机 100%、开机开启、空闲不关闭。此开关用于板上外设控制，不是 RGB；PWM P1.13 与 `ZMK_EXT_POWER` 的 P0.13 是不同线路，不能互相替代。两手同时保留显示、SPI、26px 字体配置和 8192 字节 LVGL 内存池。

nice!view 的 VCOM 极性维护由 Zephyr 驱动执行，两手配置 33 ms 串行 VCOM。`nice_view_custom` 会关闭空闲熄屏，此行为与 PWM 外设供电的空闲设置不同。

早期右手曾出现启动短暂显示后全白。恢复外设控制与双手共用猫咪后的当前方案，已由用户确认实机验证通过。

## DYA Studio

用 Chromium 打开 [DYA Studio](https://studio.dya.cormoran.works/)，通过 USB 连接接收器。固件包含 BLE 管理、Custom Settings、Fast Keymap、Device Info、Watchdog、Runtime Macro/Combo，左右键盘通过 split relay 转发配置。

接收器使用 `studio-rpc-usb-uart` 的 CDC 通道。DYA 和电脑同步软件不能同时独占同一端口；切换软件前关闭另一方的连接。

- **Debug Tool → Bootloader**：请求接收器进入 UF2 启动器。
- Nano 接收器的标准 Studio 改键入口选择 **Bootloader**：约 500 ms 后执行 BL 请求，普通按键绑定不被替换。
- 同一入口选择 **Bluetooth → BT_CLR_ALL**：清除接收器保存的主机配对及 split peer 并重启。两手若仍保存旧配对，也需分别清除。

以上管理操作依赖应用和 USB 正常运行；应用不启动时使用下面独立 BL 的短插拔。Fast Keymap 的所有批量操作不保证经过标准改键钩子。

## 独立 BL 与恢复入口

独立短插拔检测在 BL 内执行，不依赖 ZMK、DYA 或 HID：

1. 插入后不到 1 秒拔下。
2. 再插入，不到 1 秒拔下。
3. 第三次插入后保持连接，等待 UF2 磁盘出现。

BL 设计窗口约为 2 秒，使用不到 1 秒的操作更稳妥。正常保持上电约 2 秒后清零计数、启动应用。拔下后没有持续供电，不能计算两次插入之间的断电时长。软件、看门狗或复位引脚重启不计入冷上电次数。

普通 `velvet_nano_dongle.uf2` 只更新应用，**不会更新 BL**。应用中的旧“等待约 2 秒、10 秒内拔下”机制是另一套依赖应用运行的备用机制，不等同于独立 BL 的短插拔。

## BL 更新与文件下载

详见 [Bootloader 安装与更新说明](bootloader/README.md)。以下均仅适用于这块 nRF52833 小接收器，不适用于左右 nRF52840 键盘。

| 文件/包 | 使用方式 | 验证状态 |
|---|---|---|
| [原已验证全量恢复 HEX](bootloader/firmware/nano33_replug_FULL_RECOVERY.hex) | J-Link/SWD 全量恢复后再刷应用；会清除应用和设置 | 有实机通过记录；磁盘名 NANO33TEST；仍有旧 USB 超时问题 |
| [新版 BL-only HEX](bootloader/updates/nano-dongle-macos/nano_dongle_BL_ONLY.hex) | J-Link/SWD 仅写 BL 地址范围，保留 MBR/UICR/应用 | 含改名和 USB 超时修正；用户确认实机通过 |
| [两步 UF2 更新 ZIP](bootloader/updates/nano-dongle-macos/Nano_Dongle_UF2_Update.zip) | 现有兼容 BL 的专用自更新，严格按 01→02 顺序 | 实机验证通过；会清除设置与配对 |

新版显示名为 **Nano Dongle**，UF2 卷标为 **NANO DONGLE**，包含独立短插拔与 macOS/Finder 复制过程中 USB 已连接时不再被 30 秒定时器强制复位的修正。改变 VID 并非此次修正方式。

两步 UF2 单独下载：[01 更新 BL](bootloader/updates/nano-dongle-macos/01_nano_dongle_bootloader_update.uf2)、[02 恢复应用](bootloader/updates/nano-dongle-macos/02_velvet_nano_dongle_restore.uf2)。**02 是该更新包配套的旧应用恢复镜像，不是最新猫咪套装固件，也不是 settings reset**；完成恢复后再更新目标版本的同批正常应用。

文件没有重新编译，保留已有内容；[SHA256SUMS](bootloader/updates/nano-dongle-macos/SHA256SUMS) 与 [validation.json](bootloader/updates/nano-dongle-macos/validation.json) 可用于核对来源、格式、文件内容和用户实机确认记录。新版更新文件与旧全量恢复 HEX 的功能差异见上表。

## 扫描仪与 Cube

接收器使用一个传统 BLE 广播实例，完整名称固定为 **Velvet46**。标准状态与左右手遥测按 1:1 交替发送；活动周期 100 ms、空闲周期 500 ms。扫描仪使用总 WPM，Cube 使用左右手独立 WPM 与电量。

左右手通过现有 split relay 报告物理左右标识，避免按连接顺序猜电量来源；0% 仍为有效电量。名称、两手电量及 WPM 广播已经抓包核对，扫描仪/Cube 显示已获用户实机确认正常。

接收器使用内部 RC 32 kHz 时钟及自动校准，避免无低频晶振硬件被配置为 XTAL 后启动阻塞；nRF52833 仍禁用额外扩展广播实例。

## 密码宏重复末尾字符

Dongle 模式的宏由接收器执行。原接收器队列被限制为 16 项，现有 11 次 tap 需要 22 个按下/松开事件，队列满可能丢弃字符或松开事件，导致最后一个字符持续重复。

已将接收器 shield 配置和构建覆盖参数统一调整为 ZMK 默认 64 项，未更改宏内容或默认时序。使用实际队列代码的无敏感测试：16 项时丢弃 5 个事件并残留一个未释放键，64 项完整执行 22 个事件。此修正已由用户确认实机验证通过。

## 验证与更新范围

- 独立 BL 的原全量恢复 HEX：见固定 SHA256 和实机记录。
- 新版 BL-only/两步 UF2：文件校验与用户实机验证均通过。
- 双手猫咪、宏队列、显示配置、DYA 与扫描仪/Cube 遥测：用户确认实机验证通过。
- 确认来源：用户于 2026-10-19 在本次对话确认全部实机通过；该日期为确认日期。
- 本次只更新 README、BL 附件和校验信息，不回退分支代码，不创建 release，不触发任何 Actions。

## DYA 功能接入

已补齐 Runtime Tap Dance 及常用 DYA 模块的显式配置，保留现有键位。详见 [功能审计与使用说明](docs/dya-feature-audit.md)。构建仍手动触发。
