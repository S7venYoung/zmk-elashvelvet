#!/usr/bin/env python3
"""Populate standard Prospector status with physical-half telemetry."""
from pathlib import Path
import sys

def patch(source):
    if "VELVET_DONGLE_STATUS_FIELDS" in source:
        return source
    include = '#include <zmk/activity.h>'
    call = '    build_manufacturer_payload();'
    if source.count(include) != 1 or source.count(call) != 1:
        raise ValueError("Unexpected Prospector sender")
    return source.replace(include, include+'\n#include "fight_status.h"', 1).replace(call, call+'\n'+"    /* VELVET_DONGLE_STATUS_FIELDS: both physical halves report to USB central. */\n    uint8_t half_wpm[2], half_battery[2], half_valid;\n    fight_telemetry_read(half_wpm, half_battery, &half_valid);\n    manufacturer_data.wpm_value = MIN((unsigned int)half_wpm[0] + half_wpm[1], 255);\n    if (half_valid & BIT(1)) manufacturer_data.battery_level = half_battery[0];\n    if (half_valid & BIT(2)) manufacturer_data.peripheral_battery[0] = half_battery[1];\n    if (manufacturer_data.wpm_value) {\n        last_activity_time = k_uptime_get_32();\n        is_active = true;\n    }\n", 1)

if __name__ == "__main__":
    path = Path(sys.argv[1])
    path.write_text(patch(path.read_text()))
