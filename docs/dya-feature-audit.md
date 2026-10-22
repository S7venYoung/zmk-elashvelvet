# DYA 功能审计（2026-10-22）

正常键盘功能接入：BLE 管理、按键/层编辑、Fast Keymap、Custom Settings、Device Info、Watchdog、Runtime Macro/Combo、Runtime Tap Dance、按键输入流、物理布局、默认层/OS 识别及矩阵扫描诊断。新增项显式启用，Actions 检查实际 .config 和 Tap Dance 目标文件，防止只有模块却没有 RPC。

Runtime Tap Dance 使用上游命名条目 API v2：16 个命名条目、1024 字节池、最多 8 个同时运行序列。支持单/双/三击、RAM 应用、保存/放弃、重命名和删除。主控通过 rtd 行为节点向 DYA 暴露，现有键位、静态 Tap Dance 和宏不替换。先在 DYA 创建，再将对应 ID 分配给按键；ID 可复用在多个按键。

上游 Tap Dance 与 Custom Settings 共享池依赖固定到本次审计提交，ZMK 版本/硬件引脚不升级。无屏接收器和普通中央键盘负责执行，左右手 peripheral 只上报按键、扫描诊断、Watchdog/settings relay，不重复跑宏或 Tap Dance。Cube 的实际执行由 ESP32-S3 主控实现；此分支的左右手不能替代 Cube 主控功能。

默认层范围对应现有 BASE/NVA/SYS（0–2）；OS 识别启用，不自动改变现有默认层或 OS 专用层映射。未知操作系统保留未知。

按既有要求，不新增编码器、轨迹球、指针传感器。DYA 网页的云同步/分享、撤销和版本历史属于客户端功能。Devtool 的虚拟按键注入、全键事件捕获和日志捕获属于上游明确标注的开发/测试功能，不在日常固件自动启用；不能把这些开发入口或不存在的硬件报告为已支持。

普通升级无需刷 reset 或更新 BL。仅在用户要求时触发 Actions；源码审计不等于固件构建或实机测试完成。

main 同时清除原版残留的 EC11、PMW3610、Runtime Sensor Rotate/Input Processor 及鼠标行为绑定；保留原有矩阵、屏幕供电和所有键盘按键，原鼠标功能位置改为透明。
