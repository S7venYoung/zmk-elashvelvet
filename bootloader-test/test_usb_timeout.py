#!/usr/bin/env python3
"""Compile and exercise the actual DFU timer callback with mocked hardware."""
from pathlib import Path
import subprocess, sys, tempfile

def run(source, expect_fixed):
    start = source.index("static void dfu_startup_timer_handler")
    end = source.index("/**@brief   Function for waiting", start)
    callback = source[start:end]
    harness = """
#include <assert.h>
#include <stdbool.h>
#define NRF_USBD 1
#define DFU_TIMEOUT 7
static bool m_cancel_timeout_on_usb, mounted, dfu_startup_packet_received;
static int resets, timeouts;
typedef struct { int status_code; } dfu_update_status_t;
static bool tud_mounted(void) { return mounted; }
static void NVIC_SystemReset(void) { resets++; }
static void bootloader_dfu_update_process(dfu_update_status_t status) {
    assert(status.status_code == DFU_TIMEOUT); timeouts++;
}
""" + callback + """
static void clear(void) { resets = timeouts = 0; }
int main(void) {
    clear(); m_cancel_timeout_on_usb = true; mounted = true;
    dfu_startup_packet_received = false;
    dfu_startup_timer_handler(0);
    assert(resets == 0 && timeouts == 0);
    clear(); mounted = false; dfu_startup_packet_received = true;
    dfu_startup_timer_handler(0);
    assert(resets == 0 && timeouts == 0);
    clear(); mounted = false; dfu_startup_packet_received = false;
    dfu_startup_timer_handler(0);
    assert(resets == 0 && timeouts == 1);
    clear(); m_cancel_timeout_on_usb = false; mounted = true;
    dfu_startup_timer_handler(0);
    assert(resets == 0 && timeouts == 1);
    return 0;
}
"""
    with tempfile.TemporaryDirectory() as temp:
        p = Path(temp); (p/"test.c").write_text(harness)
        subprocess.run(["cc","-Wno-unused-function","-Wno-unused-parameter",str(p/"test.c"),"-o",str(p/"test")],check=True)
        result = subprocess.run([str(p/"test")],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        assert (result.returncode == 0) == expect_fixed, result.stderr.decode()
    return result.returncode

if __name__ == "__main__":
    source = Path(sys.argv[1]).read_text()
    assert "APP_TIMER_TICKS(timeout_ms), NULL" in source
    run(source, True)
    print("Actual DFU timeout callback tests passed: mounted USB, active transfer, idle and serial timeout")
