#!/usr/bin/env python3
"""Trace Pad BLE transitions in the RTT diagnostic build only."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text()
marker = "/* EYELASH_PAD_RTT_TRACE */"
if marker in source:
    sys.exit(0)

hooks = (
    ("    const int err = start_advertising(low_duty_advertising);",
     '    eyelash_pad_rtt_trace("adv_start", err, low_duty_advertising);'),
    ("    int err = bt_le_adv_stop();",
     '    eyelash_pad_rtt_trace("adv_stop", err, is_connected);'),
    ("    is_connected = (err == 0);",
     '    eyelash_pad_rtt_trace("connected_cb", err, is_connected);'),
    ("static void recycled(void) {",
     '    eyelash_pad_rtt_trace("recycled_cb", 0, is_connected);'),
    ("    LOG_DBG(\"Disconnected from %s (reason 0x%02x)\", addr, reason);",
     '    eyelash_pad_rtt_trace("disconnected_cb", reason, is_connected);'),
    ("static void pad_advertising_recovery_cb(struct k_work *work) {",
     '    eyelash_pad_rtt_trace("recovery", enabled, is_connected);'),
    ("    enabled = en;",
     '    eyelash_pad_rtt_trace("transport_enabled", en, is_connected);'),
)
for anchor, trace in hooks:
    if source.splitlines().count(anchor) != 1:
        sys.exit(f"Unexpected Pad trace hook: {anchor}")
    source = source.replace("\n" + anchor + "\n", "\n" + anchor + "\n" + trace + "\n", 1)

path.write_text(marker + "\nextern void eyelash_pad_rtt_trace(const char *event, int result, int state);\n" + source)
