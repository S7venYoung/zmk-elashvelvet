"""Delay UF2 completion until the host has finished a quiet WRITE10 window."""
from pathlib import Path
import sys

SUPPORT = """
/* VELVET_UF2_FINISH_GRACE: keep servicing USB after the final WRITE10 CSW. */
#include "app_timer.h"

static uint32_t uf2_last_write_tick;
static bool uf2_finish_pending;
static bool uf2_finish_done;

static void nano_uf2_finish(void);

void nano_uf2_finish_poll(void) {
  if (uf2_finish_pending && !uf2_finish_done &&
      app_timer_cnt_diff_compute(app_timer_cnt_get(), uf2_last_write_tick) >=
          APP_TIMER_TICKS(1500)) {
    uf2_finish_pending = false;
    uf2_finish_done = true;
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
        source = replace(source, '#include "bootloader.h"', '#include "bootloader.h"\n' + SUPPORT)
        source = replace(source, "  (void) lun;\n\n  uint32_t count = 0;",
                         "  (void) lun;\n  uf2_last_write_tick = app_timer_cnt_get();\n  uf2_finish_pending = false;\n\n  uint32_t count = 0;")
        begin = source.index("      dfu_update_status_t update_status;", source.index("if (_wr_state.numWritten >= _wr_state.numBlocks)"))
        end = source.index("      led_state(STATE_WRITING_FINISHED);", begin) + len("      led_state(STATE_WRITING_FINISHED);")
        finish = source[begin:end]
        source = source[:begin] + """      if (!uf2_finish_done) {
        uf2_last_write_tick = app_timer_cnt_get();
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
                         "      tud_cdc_write_flush();\n      extern void nano_uf2_finish_poll(void);\n      nano_uf2_finish_poll();")
        path.write_text(source)

if __name__ == "__main__":
    patch(sys.argv[1])
