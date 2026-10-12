# Velvet46 ZMK 配置

这是 Velvet46 的 ZMK 0.4 / Zephyr 4.1 配置。左右键盘各自使用 Nice!View。`velvet_nano_dongle` 让无屏的 nice!nano K（nRF52833）担任 USB split central，通过 BLE 连接左右键盘 peripheral；接收器提供 DYA Studio 和 USB 键盘连接。

DYA Studio 模块包括 BLE 管理、Custom Settings、Fast Keymap、Device Info、Watchdog、Runtime Macro 和 Runtime Combo。左右手 peripheral 转发设置。配置不包含编码器、轨迹球或鼠标控制功能。

## Actions 固件

Actions artifact `firmware` 只包含 Dongle 模式固件和设置重置固件，UF2 文件直接平铺在压缩包根目录：

- `velvet_nano_dongle.uf2`：Nano K USB 接收器 / split central
- `velvet_left_dongle.uf2`、`velvet_right_dongle.uf2`：dongle 模式左右手 peripheral
- `settings_reset_nano.uf2`：清除接收器设置和配对
- `settings_reset.uf2`：清除 nice!nano 左右手保存的设置和配对

Dongle 模式的接收器和左右手应刷写同一次 Actions 生成的固件。清除旧配对时，接收器使用 `settings_reset_nano.uf2`，键盘使用 `settings_reset.uf2`。DYA Studio 通过 USB 连接接收器，在 Chromium 打开 <https://studio.dya.cormoran.works/>。

### Nano 接收器 DYA USB 连接

Nano 接收器使用 `studio-rpc-usb-uart` 启用 USB CDC Studio 通道。RPC 收发及自定义请求缓冲为 256 字节，RPC 线程栈为 6000 字节；构建参数固定蓝牙 ACL/事件/L2CAP 发送缓冲数量为 3/6/4，避免通用键盘配置覆盖接收器的内存预算。接收器无屏幕，左右键盘保留各自屏幕。

### 无按键接收器进入 Bootloader

Nano K 接收器没有按键，可用 USB 短插拔序列进入 UF2 Bootloader：先插入 USB，等待约 2 秒后在 10 秒内拔下；再插入、等待约 2 秒并在 10 秒内拔下；第三次插入后会自动进入 Bootloader。每次插入后保持连接超过 10 秒，会清除已记录的序列。刷写完固件后重新插入即可正常使用。

接收器拔下 USB 后没有持续供电，因此固件无法测量两次插入之间的断电时长。请连续完成上述动作；长时间断电后再次插入并保持连接超过 10 秒，也会清除可能残留的序列。此功能只编入 Nano 接收器固件，不影响左右手固件。只有实际提供 RST/DFU 入口的板子才能用硬件复位进入启动器；这只接收器的 GND/SWD/SWC/VCC 焊盘是 SWD 调试接口。此插拔功能依赖固件启动及 USB 枚举成功，不能恢复启动失败的固件。

### 通过 DYA Studio 进入 Bootloader

刷入此 ZMK 固件后，用 Chromium 打开 DYA Studio，通过 USB 连接 Nano 接收器，点击 **Debug Tool → Bootloader** 即可让接收器重启进入 UF2 Bootloader。此功能使用 `zmk-module-devtool` 的 Studio RPC；仅为接收器启用，额外的按键注入、事件抓取和日志捕获均未启用。短插拔序列仍保留为 DYA 无法连接时的备用方式。

当前若接收器仍运行截图所示的 QMK/Vial 2.4G Receiver R1.3 固件，DYA 无法连接它，也无法用于首次进入 Bootloader。首次刷入需要先通过原固件或硬件支持的启动器入口进入刷机模式；确认启动器接受此板的 UF2 后再刷 `velvet_nano_dongle.uf2`。

### Nano K 启动时钟修复

接收器使用内部 RC 32 kHz 时钟和自动校准，覆盖共享键盘配置中的外部晶振选择，并使用 500 ppm 精度设置。没有 32 kHz 晶振的接收器若被配置成 XTAL，可能在启动等待低频时钟时卡住，导致 USB 不枚举。Actions 检查最终 `.config`，阻止晶振配置再次覆盖接收器。原始 HEX 的启动器入口为 `0x74000`，应用入口为 `0x1000`，与本分支分区一致；此前关于必须改为 `0x18000` 的猜测不成立。

### Studio 选择行为直接执行管理操作

仅在 Nano 接收器上，Studio 的改键界面选择 **Bootloader** 会在约 500 ms 后重启进入 BL；选择 **Bluetooth → Clear all bonds（BT_CLR_ALL）** 会清除接收器的主机配对、左右手 peer 地址并重启。普通改键照常生效；这两个管理操作不会替换或保存原按键绑定。清除后，左右手若仍保留旧配对，也需各自重置配对。此钩子作用于标准 Studio 改键请求，不承诺所有 Fast Keymap 批量操作都会经过同一入口。DYA 的 Debug Tool → Bootloader 入口仍可使用。

钩子由 Actions 在 west 拉取 ZMK 后安装；若上游 setter 结构改变，脚本会终止构建，避免静默丢失管理入口。构建成功不等于已通过实机 USB、进入 BL 和配对清除测试。
