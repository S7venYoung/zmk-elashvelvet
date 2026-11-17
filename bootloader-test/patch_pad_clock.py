"""Keep the SDK RTC alive for the Pad's UF2 quiet-window completion."""
from pathlib import Path

SUPPORT = '''
/* PAD_UF2_CLOCK: zero-timeout DFU has no SDK timers, so RTC1 otherwise stops. */
#include "app_error.h"
APP_TIMER_DEF(pad_uf2_clock_timer);
static void pad_uf2_clock_tick(void *context) { (void)context; }
void pad_uf2_clock_start(void) {
  static bool created;
  if (!created) {
    APP_ERROR_CHECK(app_timer_create(&pad_uf2_clock_timer, APP_TIMER_MODE_REPEATED,
                                    pad_uf2_clock_tick));
    created = true;
  }
  APP_ERROR_CHECK(app_timer_start(pad_uf2_clock_timer, APP_TIMER_TICKS(100), NULL));
}
'''

def patch(root):
    root = Path(root)
    msc = root / 'src/usb/msc_uf2.c'
    source = msc.read_text()
    if 'PAD_UF2_CLOCK' not in source:
        anchor = 'static uint32_t uf2_last_write_tick;'
        assert source.count(anchor) == 1
        msc.write_text(source.replace(anchor, SUPPORT + '\n' + anchor, 1))
    boot = root / 'lib/sdk11/components/libraries/bootloader_dfu/bootloader.c'
    source = boot.read_text()
    if 'pad_uf2_clock_start();' not in source:
        anchor = '    // DFU mode with timeout can be'
        assert source.count(anchor) == 1
        source = source.replace(anchor,
            '#ifdef NRF_USBD\n#if CFG_TUD_MSC\n'
            '    extern void pad_uf2_clock_start(void);\n'
            '    pad_uf2_clock_start();\n#endif\n#endif\n' + anchor, 1)
        boot.write_text(source)
