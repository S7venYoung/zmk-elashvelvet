#!/usr/bin/env python3
"""Cancel the USB startup timeout after enumeration instead of resetting."""
from pathlib import Path
import sys

def patch(path):
    path = Path(path)
    source = path.read_text()
    old = """  if (m_cancel_timeout_on_usb && tud_mounted())
  {
    NVIC_SystemReset();
    return;
  }"""
    new = """  if (m_cancel_timeout_on_usb && tud_mounted())
  {
    /* USB is mounted: cancel this one-shot timeout, never interrupt UF2. */
    return;
  }"""
    if new in source:
        return
    if source.count(old) != 1:
        raise SystemExit("Unexpected DFU timer implementation")
    source = source.replace(old, new, 1)
    start = source.index("static void dfu_startup_timer_handler")
    end = source.index("/**@brief   Function for waiting", start)
    handler = source[start:end]
    # Let DFU_TIMEOUT close the transport and the event loop reset normally.
    handler = handler.replace("    NVIC_SystemReset();\n", "")
    source = source[:start] + handler + source[end:]
    old_timer = "APP_TIMER_TICKS(30000), NULL"
    if source.count(old_timer) != 1:
        raise SystemExit("Unexpected DFU timer duration")
    source = source.replace(old_timer, "APP_TIMER_TICKS(timeout_ms), NULL", 1)
    path.write_text(source)

if __name__ == "__main__":
    patch(sys.argv[1])
