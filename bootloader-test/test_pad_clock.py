"""Exercise real Pad clock and quiet-window helpers with an initially stopped RTC."""
from pathlib import Path
import subprocess
import tempfile
from patch_pad_clock import SUPPORT as CLOCK
from patch_uf2_finish import SUPPORT as FINISH

program = r'''
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <assert.h>
static bool running;
static unsigned now, created, started, completions;
static struct { bool aborted; } _wr_state;
#define APP_TIMER_DEF(name) static int name
#define APP_TIMER_MODE_REPEATED 1
#define APP_TIMER_TICKS(ms) (ms)
#define APP_ERROR_CHECK(err) assert((err) == 0)
static int app_timer_create(int *timer, int mode, void (*handler)(void *)) {
  (void)timer; assert(mode == 1); handler(NULL); created++; return 0;
}
static int app_timer_start(int timer, unsigned ticks, void *context) {
  (void)timer; (void)context; assert(ticks == 100); running = true; started++; return 0;
}
static unsigned app_timer_cnt_get(void) { return now; }
static unsigned app_timer_cnt_diff_compute(unsigned a, unsigned b) { return (a-b)&0xffffff; }
static void flash_nrf5x_flush(bool wait) { assert(wait); }
static void advance(unsigned ticks) { if (running) now = (now + ticks)&0xffffff; }
''' + CLOCK.replace('#include "app_error.h"', '') + FINISH.replace('#include "app_timer.h"', '').replace('#include "flash_nrf5x.h"', '') + r'''
static void nano_uf2_finish(void) { completions++; }
int main(void) {
  uf2_finish_pending = true;
  uf2_last_write_tick = app_timer_cnt_get();
  advance(2000); nano_uf2_finish_poll(); assert(completions == 0); // old stalled RTC
  pad_uf2_clock_start(); assert(running && created == 1);
  advance(999); nano_uf2_finish_poll(); assert(completions == 0);
  advance(1); nano_uf2_finish_poll(); assert(completions == 1);
  pad_uf2_clock_start(); assert(created == 1 && started == 2);
  advance(2000); nano_uf2_finish_poll(); assert(completions == 1);
  return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
    source = Path(d) / 'test.c'; binary = Path(d) / 'test'
    source.write_text(program)
    subprocess.run(['cc','-Wall','-Wextra','-Werror',str(source),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
print('Pad zero-timeout RTC: reproduced stalled completion; clock start, 1-second completion and repeat init passed')
