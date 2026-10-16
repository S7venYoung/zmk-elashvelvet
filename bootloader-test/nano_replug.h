/* SPDX-License-Identifier: MIT */
#pragma once
#include "replug_policy.h"
/* Reserve [0x65000,0x66000). This is outside Velvet's app and settings. */
static bool nano_journal_read(uint8_t *stage, uint32_t *slot) {
  const uint32_t *words = (const uint32_t *)NANO_JOURNAL_ADDR;
  *stage = 0;
  *slot = 0;
  for (uint32_t i = 0; i < 1024; i++) {
    if (words[i] == NANO_ERASED) {
      /* No hidden foreign data after the first erased record. */
      for (uint32_t j = i; j < 1024; j++)
        if (words[j] != NANO_ERASED) return false;
      *slot = i;
      return true;
    }
    if (!nano_record_valid(words[i])) return false;
    *stage = words[i] & 0xffu;
  }
  *slot = 1024;
  return true;
}
static bool nano_journal_append(uint8_t stage) {
  uint8_t old_stage;
  uint32_t slot;
  if (!nano_journal_read(&old_stage, &slot)) return false;
  if (slot == 1024) {
    nrfx_nvmc_page_erase(NANO_JOURNAL_ADDR);
    slot = 0;
  }
  const uint32_t record = NANO_RECORD_MAGIC | stage;
  const uint32_t addr = NANO_JOURNAL_ADDR + slot * 4;
  nrfx_nvmc_words_write(addr, &record, 1);
  return *(const volatile uint32_t *)addr == record;
}
static bool nano_replug_boot(uint32_t reset_reason) {
  /* Software, watchdog and reset-pin resets must not count as unplugging. */
  if (reset_reason != 0) return false;
  uint8_t stage;
  uint32_t slot;
  if (!nano_journal_read(&stage, &slot)) return true;
  if (nano_enter_dfu(stage, true)) {
    (void)nano_journal_append(0);
    return true;
  }
  if (!nano_journal_append(nano_next_stage(stage))) return true;
  /* Complete this window inside BL even when the application will crash. */
  NRFX_DELAY_MS(2000);
  return !nano_journal_append(0);
}
