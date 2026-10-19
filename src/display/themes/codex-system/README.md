# Codex＋系统：同一套主题

`left/render.h`：Codex 剩余额度和重置倒计时。
`right/render.h`：CPU 占用、CPU 温度、内存和真实新采样趋势。

统一顶部图标状态栏和 LAYER 框。使用实际 160×68 像素重新排版；参考图的屏幕比例更宽，无法逐像素照搬。这里的图为实际 C 绘图器输出，样例数据不是实时值。

左手：

![左 Codex，样例数据](left/preview.svg)

右手：

![右系统，样例数据](right/preview.svg)

DYA 选择整套 `theme_set=1`；猫咪整套为 0。本目录两页不是两套独立主题，不额外分配两个同时运行的帧缓冲。
