"""Backport Adafruit 125763c USB-idle UF2 completion to the pinned Nano fork.

Preserve the old fork's DFU fields and bootloader-copy address constants.
"""
from pathlib import Path
import sys

SUPPORT = """
/* VELVET_UF2_FINISH_GRACE: keep servicing USB after the final WRITE10 CSW. */
#include "app_timer.h"
#include "flash_nrf5x.h"

static uint32_t uf2_last_write_tick;
static bool uf2_finish_pending;
static bool uf2_finish_done;
static bool uf2_write_active;

static void nano_uf2_finish(void);

void nano_uf2_finish_poll(void) {
  if (uf2_finish_pending && !uf2_finish_done && !uf2_write_active && !_wr_state.aborted &&
      app_timer_cnt_diff_compute(app_timer_cnt_get(), uf2_last_write_tick) >=
          APP_TIMER_TICKS(1000)) {
    uf2_finish_pending = false;
    uf2_finish_done = true;
    flash_nrf5x_flush(true);
    nano_uf2_finish();
  }
}
"""

def replace(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"Unexpected UF2 completion source: {old!r}")
    return source.replace(old, new, 1)

def patch(root):
    root = Path(root)
    path = root / "src/usb/msc_uf2.c"
    source = path.read_text()
    if "VELVET_UF2_FINISH_GRACE" not in source:
        source = replace(source, "static WriteState _wr_state = { 0 };",
                         "static WriteState _wr_state = { 0 };\n" + SUPPORT)
        source = replace(source, "  uint16_t resplen = 0;", "  int32_t resplen = 0;")
        source = replace(source, "    resplen = -1;", "    return -1;")
        source = replace(source, "    case SCSI_CMD_PREVENT_ALLOW_MEDIUM_REMOVAL:",
                         "    case 0x35: /* SYNCHRONIZE CACHE(10) */\n"
                         "      flash_nrf5x_flush(true);\n"
                         "      return 0;\n\n"
                         "    case SCSI_CMD_PREVENT_ALLOW_MEDIUM_REMOVAL:")
        source = replace(source, "  (void) lun;\n\n  uint32_t count = 0;",
                         "  (void) lun;\n  if (uf2_finish_done) return -1;\n  uf2_write_active = true;\n\n  uint32_t count = 0;")
        source = replace(source, "  static bool first_write = true;",
                         "  static bool first_write = true;\n"
                         "  uf2_write_active = false;\n"
                         "  uf2_last_write_tick = app_timer_cnt_get();\n"
                         "  if (uf2_finish_done) return;")
        begin = source.index("      dfu_update_status_t update_status;", source.index("if (_wr_state.numWritten >= _wr_state.numBlocks)"))
        end = source.index("      led_state(STATE_WRITING_FINISHED);", begin) + len("      led_state(STATE_WRITING_FINISHED);")
        finish = source[begin:end]
        source = source[:begin] + """      if (!uf2_finish_done) {
        uf2_finish_pending = true;
      }""" + source[end:]
        anchor = "// Invoked when received SCSI_CMD_READ_CAPACITY_10"
        source = replace(source, anchor,
                         "static void nano_uf2_finish(void) {\n" + finish + "\n}\n\n" + anchor)
        path.write_text(source)
    path = root / "lib/sdk11/components/libraries/bootloader_dfu/bootloader.c"
    source = path.read_text()
    if "nano_uf2_finish_poll();" not in source:
        source = replace(source, "      tud_cdc_write_flush();",
                         "      tud_cdc_write_flush();\n#if CFG_TUD_MSC\n      extern void nano_uf2_finish_poll(void);\n      nano_uf2_finish_poll();\n#endif")
        path.write_text(source)

if __name__ == "__main__":
    patch(sys.argv[1])
