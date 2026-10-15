# Velvet nice!nano OLED Fight Dongle

本分支 `codex/nano-dongle-fight` 基于 `codex/nano-dongle`，接收器改为 **nice!nano nRF52840**，使用 ZMK 0.4 / Zephyr 4.1 和 DYA。**不要给原来的 nRF52833 小接收器刷本分支固件。**

## 固件与刷入

Actions 的 `firmware` 压缩包直接提供四个 UF2 文件：

- `velvet_nano_dongle_fight.uf2`：nice!nano nRF52840 接收器 + OLED。
- `velvet_left_dongle.uf2`、`velvet_right_dongle.uf2`：左右键盘，保留原 Nice!View 配置。
- `settings_reset.uf2`：nice!nano nRF52840 清空设置；之后需重刷对应正常固件并重新配对。

进入 UF2 启动器后，把对应 UF2 复制到 `NICENANO` 盘；本分支使用原生 `nice_nano//zmk` 构建，不修改 nRF52833 文件的 family ID 来绕过检查。

## OLED 接线与 Fight 主题

参考 [Sofle fighting-theme 分支](https://github.com/S7venYoung/zmk-sofle-dongle-dya/tree/fighting-theme)，使用 **SH1106、128×64、I2C 地址 0x3c**；其他控制器或屏幕尺寸需要修改 overlay。

| OLED | nice!nano |
| --- | --- |
| SDA | P0.17 |
| SCL | P0.20 |
| GND | GND |
| VCC | 3.3V |

接收器 OLED 显示 Kyo/Terry 双角色动画，左右手按键速度分别决定角色动作；顶部显示两侧电量及 U/B 输出状态。已将 Sofle 的按键分侧逻辑改为 Velvet 的 61 键顺序。左右手屏幕沿用原配置，Fight 界面在接收器上。

主题来源为 [zmk-dongle-fighter-theme](https://github.com/hitsmaxft/zmk-dongle-fighter-theme)，锁定 Sofle 使用的 `7f59dc76d56a054e81b6dd905d69fd5f0d360265`。本分支复用 Sofle 的轻量双角色渲染器与预生成素材，不需要商业 ROM 或完整动画 provider ABI。`scripts/generate_dual_fighter_assets.py` 可从该主题的 `assets/character_bitmaps` 重新生成 `boards/shields/dongle_display/widgets/fight_assets.c`。

## DYA 与无按键管理

保留 Custom Settings、Fast Keymap、Device Info、Watchdog、Runtime Macro/Combo、BLE 管理与 Settings RPC。未启用编码器、轨迹球及相关 DYA 功能。USB 使用 `studio-rpc-usb-uart`。

保留 Studio 编辑绑定时的管理钩子：选择 Bootloader 后延迟重启进入启动器；选择蓝牙清除全部配对时清除配对并重启。管理动作不替换所选位置的原按键。还保留短插拔进入启动器的实现；完全断电时无法严格计算拔出期间的 10 秒。nice!nano 的物理复位入口仍可用于恢复。

构建仅使用 GitHub Actions；编译通过不代表屏幕接线、USB 枚举和无线配对已完成实机验证。

## 独立扫描仪发现与状态广播

接收器提供与 `codex/zmk04-dya-Prospector` 一致的 Prospector 状态广播，以及 Fight 左右手遥测。独立扫描仪无需与接收器配对即可发现 `Velvet46`，接收层、输出状态、修饰键、WPM 和左右手电量。频道为 0（通用广播），空闲状态每秒更新。

Dongle 按 AUX central 配置：左手来自 peripheral 0，右手来自 peripheral 1；接收器自身不冒充右手电池。Fight 遥测分别统计 Velvet 61 键的左右手 WPM，零电量有效、尚未收到的电量保持无效。两侧未全部连接时，Prospector 状态广播使用短广播/静默窗口，为键盘重连让出无线时间；此期间发现可能较慢。

只更新接收器即可获得广播功能，原有左右手固件不变。扫描仪若限定了频道或选中了其他键盘，需要切回频道 0/选择 Velvet46。DYA、进入 BL、清除配对及本分支原有显示配置保留。扫描仪发现与数值显示仍需实机验证。
