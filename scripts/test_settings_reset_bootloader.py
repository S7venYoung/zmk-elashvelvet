#!/usr/bin/env python3
"""Exercise the patched C callbacks with mocked erase/bootmode/reboot APIs."""
from pathlib import Path
import subprocess
import tempfile
from patch_settings_reset_bootloader import ORIGINAL, patch

STUB = r'''
#include <errno.h>
#define CONFIG_ZMK_LOG_LEVEL 3
#define CONFIG_ZMK_SETTINGS_RESET_ON_START_INIT_PRIORITY 80
#define SYS_INIT(...)
#define LOG_MODULE_DECLARE(...)
#define LOG_ERR(...) ((void)0)
#define ARG_UNUSED(x) ((void)(x))
#define K_MSEC(x) (x)
#define BOOT_MODE_TYPE_BOOTLOADER 1
#define SYS_REBOOT_WARM 0
struct k_work { int unused; };
#define K_WORK_DELAYABLE_DEFINE(name, fn) struct k_work name
static int erase_error, boot_error, schedule_error;
static int erase_count, schedule_count, boot_count, reboot_count;
static int zmk_settings_erase(void) { erase_count++; return erase_error; }
static int bootmode_set(int mode) { assert(mode == 1); boot_count++; return boot_error; }
static void sys_reboot(int type) { assert(type == 0); reboot_count++; }
static int k_work_reschedule(struct k_work *w, int delay) {
    (void)w; assert(delay == 1000); schedule_count++; return schedule_error;
}
'''
HARNESS = r'''
static void clear(void) {
    erase_error = boot_error = schedule_error = 0;
    erase_count = schedule_count = boot_count = reboot_count = 0;
}
int main(void) {
    clear();
    assert(velvet_reset_settings() == 0 && erase_count == 1);
    assert(velvet_reset_finish() == 0 && schedule_count == 1);
    assert(boot_count == 0 && reboot_count == 0);
    velvet_reset_enter_bootloader(&velvet_reset_boot_work);
    assert(boot_count == 1 && reboot_count == 1);
    clear(); erase_error = -EIO;
    assert(velvet_reset_settings() == -EIO);
    assert(velvet_reset_finish() == -EIO && schedule_count == 0);
    assert(boot_count == 0 && reboot_count == 0);
    clear(); boot_error = -ENODEV;
    velvet_reset_enter_bootloader(&velvet_reset_boot_work);
    assert(boot_count == 1 && reboot_count == 0);
    clear(); schedule_error = -EINVAL;
    assert(velvet_reset_settings() == 0);
    assert(velvet_reset_finish() == -EIO && reboot_count == 0);
    return 0;
}
'''
with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    source = root / 'reset.c'
    source.write_text('#include <zephyr/init.h>\n#include <zmk/settings.h>\n' + ORIGINAL + '\n')
    patch(source)
    once = source.read_text()
    patch(source)
    assert once == source.read_text(), 'patch must be idempotent'
    for name in ('zephyr/init.h', 'zmk/settings.h', 'zephyr/kernel.h',
                 'zephyr/logging/log.h', 'zephyr/retention/bootmode.h',
                 'zephyr/sys/reboot.h'):
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('')
    source.write_text('#include <assert.h>\n' + STUB + once + HARNESS)
    subprocess.run(['cc', '-Wall', '-Wextra', '-Werror', '-I', str(root),
                    str(source), '-o', str(root / 'test')], check=True)
    subprocess.run([str(root / 'test')], check=True)
    source.write_text('unexpected source')
    try:
        patch(source)
    except SystemExit:
        pass
    else:
        raise AssertionError('unknown source must fail closed')
print('Settings reset success/failure, delayed reboot, bootmode failure and patch checks passed')
