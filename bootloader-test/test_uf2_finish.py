"""Host checks for the actual delayed completion helper and patch anchors."""
import sys
import subprocess
import tempfile
from pathlib import Path
from patch_uf2_finish import SUPPORT, patch

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    msc = root / "src/usb/msc_uf2.c"
    boot = root / "lib/sdk11/components/libraries/bootloader_dfu/bootloader.c"
    msc.parent.mkdir(parents=True)
    boot.parent.mkdir(parents=True)
    msc.write_text((Path(sys.argv[1]) / "src/usb/msc_uf2.c").read_text())
    boot.write_text((Path(sys.argv[1]) / "lib/sdk11/components/libraries/bootloader_dfu/bootloader.c").read_text())
    patch(root)
    first = msc.read_text(), boot.read_text()
    patch(root)
    assert first == (msc.read_text(), boot.read_text())
    assert first[0].count("bootloader_dfu_update_process(update_status);") == 2
    assert first[0].index("static void nano_uf2_finish(void) {") > first[0].index("void tud_msc_write10_complete_cb")
    assert "int32_t resplen = 0;" in first[0]
    assert "case 0x35:" in first[0]
    assert "resplen = -1;" not in first[0]
    assert "if (uf2_finish_done) return -1;" in first[0]
    assert first[1].count("#if CFG_TUD_MSC") >= 1
    program = """
#include <stdbool.h>
#include <stdint.h>
#include <assert.h>
static uint32_t now;
static int completions, flushes;
static struct { bool aborted; } _wr_state;
static void flash_nrf5x_flush(bool wait) { assert(wait); flushes++; }
#define APP_TIMER_TICKS(n) (n)
static uint32_t app_timer_cnt_get(void) { return now; }
static uint32_t app_timer_cnt_diff_compute(uint32_t a, uint32_t b) {
  return (a - b) & 0xffffff;
}
""" + SUPPORT.replace('#include "app_timer.h"', '').replace('#include "flash_nrf5x.h"', '') + """
static void nano_uf2_finish(void) { completions++; }
int main(void) {
  nano_uf2_finish_poll(); assert(completions == 0);
  uf2_finish_pending = true; uf2_last_write_tick = 100;
  now = 1099; nano_uf2_finish_poll(); assert(completions == 0);
  uf2_last_write_tick = 1000;
  now = 1999; nano_uf2_finish_poll(); assert(completions == 0);
  now = 3000; uf2_write_active = true;
  nano_uf2_finish_poll(); assert(completions == 0);
  uf2_write_active = false; uf2_last_write_tick = now;
  now = 3999; nano_uf2_finish_poll(); assert(completions == 0);
  now = 4000; _wr_state.aborted = true;
  nano_uf2_finish_poll(); assert(completions == 0);
  _wr_state.aborted = false;
  nano_uf2_finish_poll(); assert(completions == 1 && flushes == 1);
  uf2_finish_pending = true;
  nano_uf2_finish_poll(); assert(completions == 1);
  uf2_finish_done = false; uf2_last_write_tick = 0xffff00; now = 744;
  nano_uf2_finish_poll(); assert(completions == 2);
  return 0;
}
"""
    source = root / "test.c"
    binary = root / "test"
    source.write_text(program)
    subprocess.run(["cc", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
print("UF2 finish: quiet window, write postponement, one-shot, timer wrap and idempotence passed")
