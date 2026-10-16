# Nano33 USB DFU timeout correction

The pinned fork resets immediately when its 30-second startup timer fires with USB mounted. That contradicts the stated cancel-on-USB behavior and can interrupt a Finder transfer. The UF2 path does not set the serial packet-received flag. The correction returns from the one-shot callback when USB is mounted; idle timeout uses the normal DFU_TIMEOUT close/reset path, and the requested timeout duration is honored.

Readbacks from failed application transfers in this session contained a new prefix and old suffix, first at 0x40000 and later at 0x27000. Repeating the same application through Finder from a short-power-sequence BL entry restored USB enumeration. This supports the timeout diagnosis, but the newly built bootloader still needs hardware validation.

The reset policy and journal layout are unchanged. Existing field-tested full recovery HEX is deliberately unchanged and STILL HAS the timeout defect. New BL-only candidates contain the fix; install via SWD/J-Link at the HEX's own addresses without a full-chip erase, preserving MBR/UICR/application/settings/journal. A BL-only candidate is not the full recovery image.

Do not use the generic bootloader self-update UF2: its staging range can overlap Velvet settings and the dedicated power-cycle journal. No bootloader has been written automatically during this diagnosis.
