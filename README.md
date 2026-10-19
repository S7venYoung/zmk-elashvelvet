> 当前主题按左右配套：默认左右均为小猫咪，DYA 的 theme_set=1 选择左 Codex＋右系统信息；详见 [显示模块](src/display/README.md)。以下较早修复记录为历史说明。

> **nRF52833 实机回归记录（2026-10-16）**：扫描仪广播版 `a2ba0f2`（Actions 38746000853）刷入后 USB 不枚举，DYA 和插拔入口不可用，已撤回该版广播改动。不要刷该次构建的固件。此前实机可用版本为 `54f1444`（Actions 38214599144）；无法进入启动器时需要 SWD/J-Link 恢复原始 HEX。根因尚未确认；当前分支提供单广播修复候选，尚未确认扫描仪广播实机稳定性。独立 Bootloader 已另行通过实机验证，见下文。

# Velvet46 ZMK 配置

这是 Velvet46 的 ZMK 0.4 / Zephyr 4.1 配置。左右键盘各自使用 Nice!View。`velvet_nano_dongle` 让无屏的 nice!nano K（nRF52833）担任 USB split central，通过 BLE 连接左右键盘 peripheral；接收器提供 DYA Studio 和 USB 键盘连接。

DYA Studio 模块包括 BLE 管理、Custom Settings、Fast Keymap、Device Info、Watchdog、Runtime Macro 和 Runtime Combo。左右手 peripheral 转发设置。配置不包含编码器、轨迹球或鼠标控制功能。

## 独立短插拔 Bootloader（已实机验证）

已合入 BL 内的短插拔恢复功能：前两次冷上电在约 2 秒内拔下，第三次进入 NANO33TEST；正常上电约 2 秒后启动应用。此入口不依赖 ZMK 应用运行。

[下载已验证全量恢复 HEX](bootloader/firmware/nano33_replug_FULL_RECOVERY.hex) · [安装、分区、SHA256 和测试记录](bootloader/README.md)。首次通过 J-Link 安装；全量恢复会清除应用和配对，之后再刷应用 UF2。后续日常更新应用不必重刷 BL。

## Actions 固件

Actions artifact `firmware` 只包含 Dongle 模式固件和设置重置固件，UF2 文件直接平铺在压缩包根目录：

- `velvet_nano_dongle.uf2`：Nano K USB 接收器 / split central
- `velvet_left_dongle.uf2`、`velvet_right_dongle.uf2`：dongle 模式左右手 peripheral
- `settings_reset_nano.uf2`：清除接收器设置和配对
- `settings_reset.uf2`：清除 nice!nano 左右手保存的设置和配对

Dongle 模式的接收器和左右手应刷写同一次 Actions 生成的固件。清除旧配对时，接收器使用 `settings_reset_nano.uf2`，键盘使用 `settings_reset.uf2`。DYA Studio 通过 USB 连接接收器，在 Chromium 打开 <https://studio.dya.cormoran.works/>。

### Nano 接收器 DYA USB 连接

Nano 接收器使用 `studio-rpc-usb-uart` 启用 USB CDC Studio 通道。RPC 收发及自定义请求缓冲为 256 字节，RPC 线程栈为 6000 字节；构建参数固定蓝牙 ACL/事件/L2CAP 发送缓冲数量为 3/6/4，避免通用键盘配置覆盖接收器的内存预算。接收器无屏幕，左右键盘保留各自屏幕。

### 应用内旧插拔入口（区别于独立 BL）

以下是旧 BL 下由 ZMK 应用执行的备用机制；已安装独立 BL 时，优先使用上文约 2 秒内拔下的方式。应用内机制如下：先插入 USB，等待约 2 秒后在 10 秒内拔下；再插入、等待约 2 秒并在 10 秒内拔下；第三次插入后会自动进入 Bootloader。每次插入后保持连接超过 10 秒，会清除已记录的序列。刷写完固件后重新插入即可正常使用。

接收器拔下 USB 后没有持续供电，因此固件无法测量两次插入之间的断电时长。请连续完成上述动作；长时间断电后再次插入并保持连接超过 10 秒，也会清除可能残留的序列。此功能只编入 Nano 接收器固件，不影响左右手固件。只有实际提供 RST/DFU 入口的板子才能用硬件复位进入启动器；这只接收器的 GND/SWD/SWC/VCC 焊盘是 SWD 调试接口。此插拔功能依赖固件启动及 USB 枚举成功，不能恢复启动失败的固件。

### 通过 DYA Studio 进入 Bootloader

刷入此 ZMK 固件后，用 Chromium 打开 DYA Studio，通过 USB 连接 Nano 接收器，点击 **Debug Tool → Bootloader** 即可让接收器重启进入 UF2 Bootloader。此功能使用 `zmk-module-devtool` 的 Studio RPC；仅为接收器启用，额外的按键注入、事件抓取和日志捕获均未启用。短插拔序列仍保留为 DYA 无法连接时的备用方式。

当前若接收器仍运行截图所示的 QMK/Vial 2.4G Receiver R1.3 固件，DYA 无法连接它，也无法用于首次进入 Bootloader。首次刷入需要先通过原固件或硬件支持的启动器入口进入刷机模式；确认启动器接受此板的 UF2 后再刷 `velvet_nano_dongle.uf2`。

### Nano K 启动时钟修复

接收器使用内部 RC 32 kHz 时钟和自动校准，覆盖共享键盘配置中的外部晶振选择，并使用 500 ppm 精度设置。没有 32 kHz 晶振的接收器若被配置成 XTAL，可能在启动等待低频时钟时卡住，导致 USB 不枚举。Actions 检查最终 `.config`，阻止晶振配置再次覆盖接收器。原始 HEX 的启动器入口为 `0x74000`，应用入口为 `0x1000`，与本分支分区一致；此前关于必须改为 `0x18000` 的猜测不成立。

### Studio 选择行为直接执行管理操作

仅在 Nano 接收器上，Studio 的改键界面选择 **Bootloader** 会在约 500 ms 后重启进入 BL；选择 **Bluetooth → Clear all bonds（BT_CLR_ALL）** 会清除接收器的主机配对、左右手 peer 地址并重启。普通改键照常生效；这两个管理操作不会替换或保存原按键绑定。清除后，左右手若仍保留旧配对，也需各自重置配对。此钩子作用于标准 Studio 改键请求，不承诺所有 Fast Keymap 批量操作都会经过同一入口。DYA 的 Debug Tool → Bootloader 入口仍可使用。

钩子由 Actions 在 west 拉取 ZMK 后安装；若上游 setter 结构改变，脚本会终止构建，避免静默丢失管理入口。构建成功不等于已通过实机 USB、进入 BL 和配对清除测试。

## nRF52833 扫描仪广播修复候选

此前双广播版 a2ba0f2 在 nRF52833 上出现 USB 不枚举，尚无运行时故障日志确认根因。本次保留全部扫描字段，但取消 BT_EXT_ADV 和独立 Fight 广播实例，改为在同一个传统广播中以 4:1 交替发送标准状态/左右手遥测，共用同一个硬件 ID。频道为 0，central 为 AUX，左右手电量来自 peripheral 0/1。空闲广播不会再每帧都被名称包替换。

广播工作在 USB HID 就绪且开机满 15 秒后才运行；系统工作队列栈增至 4096，主线程栈为 2048，并开启断言和栈哨兵。短插拔恢复在广播启动前有机会完成；这不能保证恢复发生在 USB 初始化之前的故障。Actions 额外保存最终 .config、DTS、ELF、map 和依赖 SHA，便于 SWD 定位。nRF52840 Fight 分支保持原可用实现。

本候选构建通过不等于实机修复成功。若 USB 在约 15 秒后消失，说明故障与广播启动有关；可重新上电，通过两次短插拔在广播启动前进入 BL，刷回已验证的 54f1444。若上电即无法枚举，需 J-Link 读取故障状态后恢复。原已确认可用版本仍为 54f1444。

## 清除设置后自动返回启动器

`settings_reset_nano.uf2`（nRF52833 接收器）和 `settings_reset.uf2`（nice!nano nRF52840 左右键盘/接收器）是临时清除固件。新版完成清除后等待约 1 秒，自动重启进入 UF2 启动器；磁盘重新出现后，直接拖入对应设备的正常固件。reset 固件本身不提供 DYA，不需要通过 DYA 再次进入 BL。左右键盘需要分别清除、分别重刷，清除配对后应让各设备重新配对。若擦除或 BL 请求失败，不自动重启。此改动不更新或覆盖 BL，本机刷机兼容性仍以实测为准。

## Dongle 模式左右手显示

左手保留 `nice_view_custom` 与内置显示界面。右手启用 `VELVET_CAT_DISPLAY`，以 160×68 单色像素呈现猫咪、实时自身电量、与接收器的 BLE 连接状态以及当前层号。绘图使用 1360 字节压缩位图，再展开至静态 10880 字节 L8 灰度缓冲；不使用索引调色板、大尺寸 LVGL 画布或额外广播实例。

右手三颗指示点共同表示与接收器的连接状态：连接时实心、断开时空心；它们不表示电脑蓝牙 profile。电量未知时显示 `--`，真实 0% 正常显示。层号由接收器通过现有 split relay 回传，内部层 0 显示 **LAYER 1**，之后依次加 1；未收到、断开或超过 5 秒未更新时显示 `--`。收包和电量事件只保存状态，LVGL 在显示队列中按需刷新。

首次启用需更新接收器和右手，左手不必更新，也不需要清除设置或更新 BL。本次未编译及实机验证；Actions 仅手动触发，必须在用户确认后构建。界面预览见 [像素猫主题](src/display/themes/cat/preview.svg)；86% 为预览示例，固件不固定该数值。

## Dongle 扫描仪左右遥测

左右手在现有 split relay 通道内每秒发送一份带物理左右标识的 WPM/电量，接收器汇总后写入标准 Prospector 广播和 Fight 广播。无需按连接先后猜左右索引，也不把无电池接收器当右手电量。WPM 使用每半本地按键统计，报告中断 5 秒后归零；0% 电量仍有效。nRF52833 保持单广播实例。首次使用该方案需要接收器、左右手全部更新为本次构建；不需要刷 reset 或重烧 BL。此修复需实机核对屏幕、WPM 和左右电量。

## 右手猫咪主题：周期 VCOM 修复候选

实机报告：启动时可看到猫咪，随后变白，按键仍正常。对应构建 38920476660 的右手最终 DTS 没有 `serial-vcom-inversion`，链接 map 也没有 VCOM 周期线程。`nice_view_custom` 的旧 overlay 未配置这项 Zephyr 4.1 驱动属性；画面按需刷新时不能依赖 UI 重绘维持 LCD 极性。

现在仅在右手补上官方 nice!view 使用的串行 VCOM 配置：`serial-vcom-inversion`、33 ms 周期和线程优先级 11。LS0XX 驱动负责空闲指令与 SPI 总线同步，不用强制重绘猫咪、不清设置、不改接收器或左手。宿主测试使用实际 Zephyr 指令编码函数对比恒定极性与交替极性；后续手动构建还会检查最终 DTS 和周期线程符号。此候选尚未编译、未实机确认解决白屏；须用户确认后构建。

## 右手持续白屏：L8 刷新候选

最新实机反馈确认 VCOM 补丁构建 38988316782 仍只短暂显示，随后白屏且按键不恢复画面。该构建已经包含 33 ms VCOM 线程，不能继续将问题归结为缺少 VCOM；真实根因尚未确认。

本候选只替换主题图像的传递方式：将可变 I1 索引图像改为静态 L8 图像，移除刷新时的图像缓存删除，固定关闭已解码图像缓存。图案、数据、VCOM 和左右手通信不变。静态帧缓冲合计 12240 字节；L8 源可由软件绘图器直接读取，避免索引图像调色板/逐行解码路径。宿主 ASAN/UBSAN 覆盖 2000 次电量、连接和层号变化及每个输出像素、缓冲边界，未发现问题；这不是对实际 LVGL 刷新、屏幕硬件或白屏根因的验证。需要用户确认后再构建、更新右手验证。

## 右手白屏排查：恢复原板外设控制

对照 main 的 `config/velvet.conf`，原板明确保留 `CONFIG_ZMK_BACKLIGHT=y` 用于外设供电/控制，与 RGB 无关。nano 分支此前删除了该开关，右手最终配置也为关闭。DTS 中该输出为 PWM0 OUT1 / P1.13；`ZMK_EXT_POWER` 控制 P0.13，两者不能相互替代。

本次仅在右手恢复上述开关及原版的开机 100%、开机开启、空闲不关闭配置，保留猫咪主题和现有屏幕驱动。Actions 检查右手最终 backlight/PWM/LED_PWM 配置，防止设置未生效；无屏接收器仍关闭 backlight，左手不变。原板注释和配置差异是修改依据，尚无电路图或实机测试证明 P1.13 就是本次白屏根因。

用户提供的右手 UF2 与构建 38990224350 逐字节一致，该 L8 候选仍白屏。宿主 LVGL 在对齐“无默认主题”配置后，8 KiB 内存池也能连续重绘 I1/L8，因此不能以早先启用了额外主题的宿主内存错误认定实机 OOM。当前恢复硬件控制的候选尚未构建、未实机验证；仍需用户明确确认后才运行 Actions。

### 左手外设控制核对

左手同样缺少原版的 `CONFIG_ZMK_BACKLIGHT=y`，现已恢复与 main 一致的外设控制开关、开机 100%、开机开启和空闲不关闭，作用于原板 PWM P1.13。左右键盘各自在 shield 配置启用，无屏 Nano 接收器仍关闭该功能。Actions 将检查两边最终的 backlight/PWM/LED_PWM 配置。

左手继续使用内置状态界面、26px 字体、8192 字节 LVGL 内存池及 `ZMK_EXT_POWER`。当前 `nice_view_custom.conf` 会覆盖 shield 的空闲熄屏设置为关闭，本次保持该行为；它与 PWM 外设控制的空闲设置是不同开关。没有启用编码器、轨迹球或改变扫描仪广播。本次配置核对不等于实机验证，未触发构建。

## Nano 宏输入队列修正（2026-10-19）

接收器实际执行按键宏，原 nano 构建参数和 shield 配置都将 `ZMK_BEHAVIORS_QUEUE_SIZE` 缩至 16，覆盖共享配置。现有输入宏含 11 次 tap，每次需要 press/release 两个队列项。ZMK 宏实现未处理队列满的返回值，可能截断后续字符并遗漏释放；问题不在左右手的队列容量。

现将接收器队列恢复为 ZMK 默认的 64 项，同时修改构建参数、shield 配置并检查最终 `.config`。保持宏内容、键位和默认时序不变。历史 nRF52833 map 中每项为 28 字节，队列从 16 增至 64 增加约 1344 字节静态 RAM；新构建仍须通过链接检查确认总 RAM 预算，没有恢复共享配置的 512 项。

使用实际 ZMK `behavior_queue.c` 配合宿主消息队列桩运行无敏感数据的 11-tap 测试：16 项时输出 17 个事件、丢弃 5 个且残留 1 个未释放键；64 项时完整输出 22 个事件、无丢弃、无残留。宿主桩不能替代接收器 USB 和实机输入验证，本次未触发 Actions；需要用户确认后构建。

## 屏幕主题目录

每套本地屏幕主题独占 `src/display/themes/<主题名>/`，绘图代码、素材、构建规则、测试、素材生成工具和预览一起管理。目前的小猫咪主题完整保留于 [cat](src/display/themes/cat/README.md)，布局、显示内容、Kconfig 开关和左右手角色均未改变。后续新增主题使用各自目录，不覆盖小猫咪素材。

当前左手的原版内置界面来自 ZMK 上游，未复制到本地主题目录。本次只整理文件及引用，没有新增主题、增加帧缓冲或实现 DYA 动态选主题；该功能后续需要主题生命周期和设置转发支持。此次未触发 Actions。

## 左 Codex / 右系统信息与 CPU 温度

新默认界面为左手 Codex、右手系统信息（CPU、RAM、CPU 温度、趋势），小猫咪作为可选主题完整保留。三套主题各有独立目录，通过接收器 DYA Custom Settings 的 `velvet_display/left_theme`、`right_theme` 选择：0=小猫咪、1=Codex、2=系统。只有偏好设置使用 Persist，实时数据只写 RAM。

电脑端复用 `S7venYoung/prospector-codex-macos` 现有 Studio USB 通道。未知/过期数据不显示样例值，CPU 温度读取依赖 Mac 的 AppleSMC CPU 传感器支持，读不到显示 `--°C`。详细协议、预览、内存复用、同步周期和验证限制见 [显示模块](src/display/README.md)。两个仓库 Actions 均仅手动触发，此次未构建，需配套固件/应用构建及实机验证。

## 整套主题修正与新版像素排版

主题选择改为一个 `velvet_display/theme_set`：0=左右都是原小猫咪，1=左 Codex＋右系统信息（同一套主题）。取消之前的左右独立选择；默认整套小猫咪，旧的 left_theme/right_theme 不再生效。每套主题独立目录，信息套装的左右页合并在 `src/display/themes/codex-system/`。

新版信息套装改用图标状态栏、较高的 CODEX/百分比数字、较大的 CPU/RAM 标题、分区进度条和完整 LAYER 标签，按实际 160×68 重排。预览由同一 C 绘图代码生成，仍是待实机验证的候选，未触发构建。上文提及“三套主题、左右独立选择”的旧记录已由本节替代。

## 信息套装简化

按新参考图去掉屏幕上的 CODEX 字样与 CPU 趋势图，改为左右各三行：左 5H/7D/RESET，右 CPU/RAM/TEMP。采用纯色进度条，层号放入顶部 L1；CPU 温度显示整数°C。整套选择仍是 0=左右猫咪（默认），1=额度＋系统。预览和进度量程说明见 [信息套装](src/display/themes/codex-system/README.md)。此改动未触发构建，需实机验证。

简洁系统页进一步去掉 RAM 使用量/总量数字，仅显示 RAM 百分比与进度条；CPU/RAM/TEMP 三行等距对齐。此次未触发构建。
