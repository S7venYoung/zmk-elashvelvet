# Velvet 左右手：星智 Cube 中央端

分支 `zmk-esp32-cube`，基于 `zmk04-dya-Prospector-dongle`；继续沿用原硬件管脚与布局，不修改原分支。产物：

- 左手：`velvet_left_cube.uf2`
- 右手：`velvet_right_cube.uf2`
- 恢复：`settings_reset.uf2`，只在明确需要清除旧绑定时使用，不是每次更新的必需步骤。

左右手均为原生 ZMK split peripheral，不直接作为电脑中央端。Cube `S7venYoung/ESP32-S3-Cube-Scanner:codex/xingzhi-cube-dongle` 接收矩阵、执行动态 keymap/宏/组合，并通过 USB 或 BLE 向电脑输出；保留小智及主题。此前用户已验证基础硬件连接，新增 DYA 转发仍需新版实机确认。

## 协议与可选硬件

ZMK 固定 `e5c9b6915b56801193e359dd9bad4a167ce0d1b8`，原位置 GATT 不变。发现身份与能力特征通过加密读取，报告真实每半编码器数（最多两个）及每圈触发数；当前没有编码器或轨迹球，数量正常为零，不开启假驱动或改变管脚。

新版启用 Settings RPC、扫描诊断与看门狗原生 split relay；固定相关模块版本，危险崩溃注入关闭。Cube 使用原生 relay 分片及来源/请求编号，校验加密身份与连接代次，带超时和有限队列；不将解绑或删日志广播给错误设备。

其他继承模块仍可能跟随其原 revision，不声称整个 west manifest 已完全锁定。Zephyr 外围设置保存有去抖延迟，修改后不要立即断电。

## 更新与构建

USB 恢复方式沿用键盘原 bootloader。首次由旧中央端切换至 Cube 时可能需要清除旧键盘绑定后重新配对；已与同一 Cube 配对的普通固件更新不应无条件清除设置。请保留此前可用固件。Cube 与左右手必须使用匹配协议版本。

普通源码提交不自动构建。Actions 手动启动，或仅修改 `.github/cube-final-build-request` 启动本分支的最终构建；全部功能提交后统一构建，不反复消耗额度。构建产物包含左右手及 settings-reset，Cube 使用独立 ESP32 固件。编译不替代实机输入、断线释放、蓝牙重连和可选硬件验证。
