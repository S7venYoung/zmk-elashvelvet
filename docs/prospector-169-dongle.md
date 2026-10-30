# 1.69-inch no-touch Prospector Dongle

Base: codex/zmk04-dya-Prospector-dongle. This is a USB keyboard split central, not the standalone BLE Scanner. Builds only velvet_prospector_dongle_169.uf2 for XIAO nRF52840; no keyboard-half or reset images are built. Keep the existing Velvet keymap and WALL-E theme.

Photo identifies the actual panel as ST7789V3 240x280; the earlier Waveshare product link says ST7789V2, so physical color/offset/backlight validation remains necessary. Reuse the ST7789 driver and existing portrait-native geometry (240x280, offsets 0/20); the renderer retains its landscape rotation. SPI is limited to 20 MHz. This is an initial hardware profile, not a claim that V2/V3 analog initialization is identical.

| Module pin | XIAO pin |
| --- | --- |
| BLK | D6 / P1.11, active high |
| CS | D9 / P1.10 |
| DC | D7 / P1.12 |
| RES | D3 / P0.29 |
| SDA (SPI MOSI) | D10 / P1.15 |
| SCL (SPI SCK) | D8 / P1.13 |
| VCC | existing compatible supply; confirm module voltage specification |
| GND | GND |

Touch and APDS9960 nodes are disabled; brightness is fixed at 60 percent. There is no touch-based page/layer selector; keyboard/DYA actions remain available. The extra LCD shield loads last and removes the old inverted backlight polarity and redundant MISO mapping (the LCD is write-only and D9 is CS). Base pin definitions and old branches are preserved. No bootloader changes are needed.

After flashing, verify image position, colors, brightness, DYA connectivity and both-half input. Build and generated-device-tree checks do not prove physical operation. Only this receiver is built; reuse matching Velvet peripheral firmware.
