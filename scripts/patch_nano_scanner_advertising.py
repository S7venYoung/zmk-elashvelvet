#!/usr/bin/env python3
"""Patch the pinned Prospector sender for the RAM-constrained USB dongle."""
from pathlib import Path
import sys

def patch(source):
    if 'VELVET_NANO_SINGLE_ADVERTISER' in source:
        raise ValueError("Nano scanner patch already installed")
    changes = [
        ('#include <zmk/activity.h>',
         '#include <zmk/activity.h>\n#include "scanner_payload.h"\n'
         '#define VELVET_NANO_SINGLE_ADVERTISER 1'),
        ('#define NAME_ADV_INTERVAL_IDLE     1  // Every cycle when idle (30s interval)',
         '#define NAME_ADV_INTERVAL_IDLE     10  // Keep status packets flowing when idle'),
        ('    build_manufacturer_payload();', '''
    /* Give USB enumeration and the short-replug recovery path priority.
     * This is a USB-powered dongle: no status broadcasting before HID is ready.
     * Every path into this worker, including event-triggered updates, is gated.
     */
    if (k_uptime_get() < 15000 || !zmk_usb_is_hid_ready()) {
        k_work_reschedule(&adv_work, K_SECONDS(1));
        return;
    }

    build_manufacturer_payload();
    size_t payload_size;
    const uint8_t *payload = velvet_scanner_payload(
        (const uint8_t *)&manufacturer_data, sizeof(manufacturer_data),
        manufacturer_data.keyboard_id, &payload_size);
    prospector_ad[1].data = payload;
    prospector_ad[1].data_len = payload_size;
#if defined(BT_LE_ADV_OPT_FORCE_NAME_IN_AD)
    piggyback_sd[0].data = payload;
    piggyback_sd[0].data_len = payload_size;
#endif
'''),
    ]
    for old, new in changes:
        if source.count(old) != 1:
            raise ValueError("Unexpected upstream sender structure: " + old[:80])
        source = source.replace(old, new, 1)
    return source

if __name__ == "__main__":
    path = Path(sys.argv[1])
    path.write_text(patch(path.read_text()))
    print("Installed single-advertiser Nano scanner patch")
