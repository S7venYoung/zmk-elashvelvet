# Eyelash Pad RTT 诊断版

Actions 选择 `pad-rtt-diagnostic`，只用其中的
`eyelash-pad-rtt-diagnostic-ota.zip` 通过 WebDFU 更新 Pad 的应用。
保留当前 Dongle 诊断固件和配对。这个版本用于定位故障。

用适合 nRF52832 的 SWD 调试器连接 Pad 的 GND、SWDIO、SWCLK，
以及调试器要求的目标电压参考 VTref。Pad 自己供电，接线时先确认
板上焊盘和探针电压，避免让调试器和电池同时供电。
使用调试器的 RTT 工具附加到正在运行的应用，读取 RTT 通道 0。
附加时选择不复位、不暂停、不下载。若要手动指定 RTT 控制块，
在本次构建的证据包 `zmk.elf` 中查找 `_SEGGER_RTT`。

同时录 Pad 的 `PAD_RTT` 和 Dongle 的 `.11204` 日志。
先按一次 Pad 确认能看到 `key_down`，并确认 `heartbeat` 每十秒出现。
拔下 .11201 两分钟，Pad 持续供电，再插回 .11201。
如果 Pad 无法输入，按一个键并记下时间，保留故障现场。

- `disconnected_cb` 给出 HCI 原因，`recycled_cb` 表示连接对象已回收。
- `recovery` 的 result 是传输是否启用，state 是是否仍连接。
- `adv_start` 的 result 是启动返回码，state 为 1 表示使用低频路径。
- `adv_stop` 的 result 是停止返回码，state 是是否已连接。
- `key_down` 只说明本地检测到按键，不保存键值。
- 心跳来自系统工作队列。若心跳和按键日志都停，先确认 SWD 附加
  仍然正常，再判断程序或工作队列是否卡住。
