# Velvet 左右 WPM 广播

仅右中央端启用：按 Velvet 当前 default_transform 的逻辑位置分别统计左右
物理按下事件，5 秒窗口，每侧 128 条历史，WPM=count*12/5，最大255。
不计释放、编码器或主机长按重复。修改 physical layout/transform 后需要更新映射。
当前61个逻辑位置：左32、右29，不能使用 Sofle 的 position%13 映射。

右侧自身电池为 R BAT，外围 source0 为 L BAT。未收到电量事件时标记无效；
0% 为有效空电池。需实机确认电池来源和左右按键分类。

每200ms发送独立17字节厂商广播 ff ff ab ce 01：flags、4字节ID、
左右WPM、左右电量、HID修饰符、16位序号；与 Cube fighting telemetry v1 一致。
原 Prospector 26字节协议不修改，新增广播不占用连接槽。
广播名称 CUBE-FIGHT；Cube 名称过滤需允许该名称。

原 HID/Studio/Prospector 与新增广播共享无线电，须实机验证连通性和耗电。
此代码不改变 Nice View 页面，不包含街霸动画，不改变键位。

测试：cc -std=c11 tests/velvet_wpm_test.c -o /tmp/velvet-wpm-test && /tmp/velvet-wpm-test
