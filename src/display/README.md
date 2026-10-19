# 左 Codex / 右系统信息

本地主题分别位于 `themes/cat/`、`themes/codex/`、`themes/system/`。小猫咪像素素材和渲染器原样保留。新界面使用同一对压缩/L8 缓冲（1360+10880 字节），每次只绘制一个主题，切换不累计创建 LVGL 对象。

默认左手 Codex、右手系统信息。在 DYA Custom Settings 中选接收器本地 `velvet_display`：

| key | 值 | 保存方式 |
|---|---|---|
| `left_theme` | 0 小猫咪 / 1 Codex / 2 系统 | Persist 后重启保持 |
| `right_theme` | 同上 | Persist 后重启保持 |
| `host_metrics` | 18 字节电脑遥测 | 仅 MEMORY，不能将实时数据 Persist |

电脑端使用 [prospector-codex-macos](https://github.com/S7venYoung/prospector-codex-macos) 原有 Studio CDC 通道，发现 `velvet_display` 命名空间后经 `cormoran_custom_settings` 写入数据。不另开串口协议。修改主题时退出电脑同步应用，DYA 保存后退出 DYA，再启用应用；同一 CDC 端口不能被两个应用同时独占。

接收器每秒在已有 split relay 通道发布主题和状态，双方各自读取电量、连接和层号。电脑更新沿用原应用 15–60 秒节奏；90 秒无新遥测后显示未知。键盘 3 秒未收到接收器快照或 split 断开也显示未知。Codex 仍遵守电脑应用 15 分钟额度有效期；重置倒计时在接收器本地递减。CPU 图只在电脑更新序号变化时加入采样点，不重复填充旧值。

## 数据包 v1

18 字节，所有多字节数均 little-endian：

| 偏移 | 字段 |
|---|---|
| 0 | 版本 1 |
| 1 | 有效位：bit0 CPU、bit1 RAM、bit2 CPU 温度、bit3 5H、bit4 7D、bit5 reset |
| 2 | 更新序号，电脑每次更新改变，避免相同数据不产生 setting changed 事件 |
| 3–6 | CPU%、RAM%、5H 剩余%、7D 剩余% |
| 7 | 保留，必须为 0 |
| 8–9 | CPU 温度，signed int16，0.1°C，范围 -50 至 150°C |
| 10–11 | 使用内存，uint16，每单位 64 MiB |
| 12–13 | 总内存，同上；RAM 有效时必须非零且使用量不超过总量 |
| 14–17 | 5H 重置倒计时秒数，uint32 |

非法包不更新有效缓存；0 是真实值，未知通过有效位表达。重启不恢复已保存的旧遥测为在线数据。接收器不创建额外 BLE advertiser，原扫描仪/Cube 广播保持。

## 验证与限制

宿主 ASAN/UBSAN 覆盖两套渲染器全部有效位组合、0–100%、缓冲边界、非法温度/内存/数据包，以及超时和倒计时；Swift 发送样例与 C 端测试向量逐字节相同。原小猫咪渲染测试继续运行。宿主测试不验证硬件 SPI、AppleSMC 机型支持、真实 USB RPC 或 split 行为。

需要用户确认后通过 Actions 构建固件及 macOS 应用；本次没有触发构建。首次启用需更新接收器、左右键盘和电脑应用，不刷 reset、不更新 BL。此改动不是对之前白屏问题的实机修复确认。
