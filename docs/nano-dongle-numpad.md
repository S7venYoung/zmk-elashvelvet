# Nano Dongle + Velvet + Eyelash Numpad

本分支 `codex/nano-dongle-numpad` 基于 `codex/nano-dongle` 的 1460767604ea8196ed1ed191b59083020ce37ac5。

## 连接结构

电脑通过 USB 连接 Nano Dongle（nRF52833），Dongle 作为 split central，同时接收 Velvet 左半、Velvet 右半和 Eyelash 数字小键盘三个 BLE peripheral。三个设备都需要本分支的配套固件；独立蓝牙 HID 键盘不能直接作为 split 外设加入。

Dongle 的连接预算为 3 个外设 + 1 个主机连接，绑定容量为 5 个主机 + 3 个外设。没有启用启动清绑定。原左右半配对记录保留；新设备加入的槽位顺序仍需实机确认，不要为了首次调试刷 settings_reset。

## 键位与 DYA

原 Velvet 的 0–60 位置、物理坐标保持不变；密码宏已删除，其原绑定改为 `&none`，其余原有层绑定保持不变。数字区追加为位置 61–76，扫描行偏移为 5；物理 4×4 矩阵的 GPIO 和二极管方向沿用原板资料。

数字区默认键位沿用原固件：

```text
7      8  9  /
4      5  6  *
1      2  3  -
Enter  0  .  +
```

Enter 长按进入追加的 NUMPAD_FN 层（索引 3）。此层原 Velvet 区域全部透明，数字区为：

```text
NumLock  Enter  Delete  Backspace
Mute     Vol+   Vol-    无
BT0      BT1    BT2     无
透明     无     无     BLE DFU
```

这是一个共享层系统；默认绑定保证数字区在原有三个层中仍为数字，数字区 Fn 对 Velvet 透明。DYA 连接 Dongle，宏、Tap Dance、Combo 在 Dongle 执行。数字小键盘关闭这些运行时引擎、Studio、显示和指针功能，仅扫描并发送按键，减少 nRF52832 的 RAM 压力。已有自定义设置不自动擦除，升级后需在 DYA 中核对旧层以及新增 16 键的可见性和绑定。

## 固件产物

手动运行 build 工作流后，`firmware` 包含原左右半及 Dongle UF2、新的 `eyelash_numpad_peripheral.hex`。另一个 `eyelash-numpad-peripheral-swd-and-ble-dfu` 包提供：

- `eyelash-numpad-peripheral-first-install-swd.hex`：初装用合并镜像，包含 S132、启动程序及应用；先备份原固件与个人设置，再用 SWD 安装。
- `eyelash-numpad-peripheral-ota.zip`：安装配套启动程序之后使用的 Legacy BLE DFU 应用升级包。
- 应用 HEX、启动程序 HEX 和校验清单。

数字小键盘没有原生 USB；进入 BLE DFU 后用支持 Nordic Legacy DFU 的客户端上传 ZIP。配套启动程序支持上电按住物理 7+9 进入恢复模式，正常工作时可用 NUMPAD_FN 右下角进入。DFU 行为按事件来源发送至小键盘，非 nRF52832 的本地执行返回不支持。

这些是 **Dongle 外设版** 文件，不作为独立蓝牙 HID 数字小键盘使用。不要与先前独立版应用混用。角色变更后的实际配对、DFU、重连和三设备同时输入需要实机验证。

## 验证边界

本次仅完成源码和主机测试，不自动触发 GitHub Actions，也不刷机或清配对。18 项主机测试覆盖原键位保护（密码宏除外）、77 键映射、连接预算、Fn 透明、DFU 跳转、恢复按键和打包边界。实际 ARM 编译、Flash/RAM 占用，以及三外设并发稳定性尚待本分支构建和硬件验证；不能套用独立版的 RAM 数字。


## 纯网页 WebDFU（CI 构建通过，实机待验证）

本次新增 WebDFU 启动程序后，首次 SWD 镜像会使用 `Eyelash_WebDFU` 广播名和 `bootloader/web-dfu.json` 中的板级 GATT UUID。浏览器页面源码位于 `numpad/web/`，对应服务 e7a11530-9d8f-4f12-8c72-72b5d7e90901。首次刷入新版本之后，Mac Chrome 可直接选设备并传输应用，无需本地助手或安卓。

保留现有 Legacy 协议与 S132/Flash 分区，改变的是 DFU 服务标识；这不是 Secure DFU，不提供固件签名校验。只有手动进入 DFU 模式时才提供升级服务。普通 Nordic 手机客户端的默认服务查找不再适用于这个专用服务。

**4518738 构建的首次刷入 HEX 是旧启动程序。新版已在提交 e987e1c 的 Actions 41561181223 完整构建通过，请使用该次 WebDFU 镜像。** 旧版应用 OTA ZIP 的应用布局未变，可用于新版启动程序；不要用旧首次安装 HEX 覆盖新启动程序。

网页校验 ZIP 大小、应用分区、设备/S132 要求与 CRC16；传输 PRN=8 严格等待设备确认，只有设备校验通过才发送激活重启。CI 中浏览器协议测试使用合成镜像；本地另外用 4518738 的实际 OTA 包跑过同一套模拟协议测试。源码检查不能替代 ARM 编译和真实设备验证。

2026-11-03：Mac 扫描可以收到 Eyelash_WebDFU 名称，但该次广播未返回服务 UUID；网页改用名称筛选，并通过 optionalServices 授权后在连接阶段核对专用服务。Mac 只进行了广播扫描，未自动连接或刷写。

网页按用户要求仅接受本地选择的 OTA ZIP，不内置或分发固件文件。固件产物从对应 GitHub Actions 或本地构建目录单独取得；网页不上传所选文件。
