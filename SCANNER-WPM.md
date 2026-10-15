# Velvet 扫描仪模式的左右手 WPM

分支 `codex/zmk04-dya-Prospector`，不是 `zmk-esp32-cube`。右手仍是原中央端；左手仍发原生分体按键事件，矩阵、键位、配对和设备角色不变。

现有中央端使用真实按键位置分别统计左右手 WPM，17 字节制造商数据 `FF FF AB CE 01` 中，下标 10/11 分别是左右手 WPM，12/13 是左右电量，14 是修饰符，15/16 是序号。

本次将格斗广播名称从固定 `CUBE-FIGHT` 改为 `bt_get_name()` 的实际键盘名称（当前为 Velvet46），避免独立广播地址不同导致 Cube 的名称过滤器拒收。超过 29 字节的名称按 BLE legacy 上限截断并标记 shortened；Velvet46 八个字符不截断。

配套 Cube 固件必须选 `codex/nologo-xingzhi-cube-154` 的扫描仪版，并匹配 Velvet46。本次键盘代码变化仅链接到中央端，需要更新新构建的右手固件；不要求清除配对或刷 settings_reset。Cube dongle 版本及其左右手固件不在此链路使用。

代码提交不自动构建，改为手动工作流，避免反复消耗 Actions。网页/编译与真实无线接收验证要分别确认。
