# 左 Codex / 右系统信息

主题按左右配套成一套，而不是每个屏幕单独一个主题：

- `themes/cat/`：左右手都是原小猫咪，默认主题。
- `themes/codex-system/`：同一套主题，`left/` 显示 Codex，`right/` 显示系统信息及 CPU 温度。

同一时间仅绘制所选主题，共用 1360+10880 字节压缩/L8 缓冲。DYA Custom Settings 在接收器本地 `velvet_display` 只有一个主题偏好：

| key | 值 | 保存方式 |
|---|---|---|
| `theme_set` | 0 猫咪（左右都是猫咪）/ 1 Codex＋系统（左 Codex、右系统） | Persist 后重启保持 |
| `host_metrics` | 18 字节电脑遥测 | 仅 MEMORY，不能将实时数据 Persist |

原 `left_theme`、`right_theme` 已取消，旧的独立主题值不参与选择；升级后默认回到猫咪，可在 DYA 重新选择整套主题。不清除配对或其他设置。

电脑端使用 [prospector-codex-macos](https://github.com/S7venYoung/prospector-codex-macos) 原有 Studio CDC 通道，发现 `velvet_display` 命名空间后经 `cormoran_custom_settings` 写入数据。不另开串口协议。修改主题时退出电脑同步应用，DYA 保存后退出 DYA，再启用应用；同一 CDC 端口不能被两个应用同时独占。

接收器每秒在已有 split relay 通道发布主题和状态，双方各自读取电量、连接和层号。主题快照的两个原页面选择字节必须相等且为 0/1，接收器始终同时发送同一套主题。电脑更新沿用原应用 15–60 秒节奏；90 秒无新遥测后显示未知。键盘 3 秒未收到接收器快照或 split 断开也显示未知。Codex 仍遵守电脑应用 15 分钟额度有效期；重置倒计时在接收器本地递减。简洁布局不绘制 CPU 趋势图。

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

## 简洁版显示更新

信息套装不再显示 CODEX 大字，左手改为 5H/7D/RESET 三行，右手改为 CPU/RAM/TEMP 三行纯色进度条。层号统一放到顶部 L1，温度显示整数°C。RESET 条以 5 小时为满量程，温度条以 0–100°C 为量程（条饱和不截断真实文字温度）。两套主题选择、实时数据协议和双手猫咪保持不变。
