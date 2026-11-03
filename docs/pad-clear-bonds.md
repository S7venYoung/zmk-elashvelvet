# Pad 专用清配对应用

仅用于 Eyelash nRF52832 Pad + 现有 WebDFU 启动程序。通过网页选择 eyelash_numpad_clear_bonds.hex 刷入。

它使用 ZMK 内置 ZMK_BLE_CLEAR_BONDS_ON_START：在蓝牙设置加载后删除 Pad 自身所有蓝牙绑定及旧蓝牙 profile/外设地址记录。不执行 settings reset，不擦除整个存储区。会丢失 Pad 原来的所有蓝牙配对。

1. 拔掉其他 Dongle，只保留目标接收器；左右半可关闭。
2. Pad 按住 7+9 开机进入 DFU，网页选择清配对 HEX 并刷入。
3. 校验重启后等待 10 秒，让应用执行清配对。
4. Pad 再按住 7+9 开机，刷回正常 eyelash_numpad_peripheral.hex 或原 OTA ZIP。
5. 正常开机测试连接。

这是临时应用，每次启动都会清除绑定，必须刷回普通应用后才可长期使用。它不处理 Dongle 端的旧配对；如果仍不通，需要继续处理 Dongle 对应记录。硬件效果待实测。
