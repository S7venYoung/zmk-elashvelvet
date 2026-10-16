/* SPDX-License-Identifier: MIT */
#pragma once
#include <stdbool.h>
#include <stdint.h>
#define NANO_JOURNAL_ADDR 0x65000u
#define NANO_RECORD_MAGIC 0x4e330000u
#define NANO_RECORD_MASK 0xffffff00u
#define NANO_ERASED 0xffffffffu
/* Journal replay rejects foreign/torn records; never erase foreign data. */
static inline bool nano_record_valid(uint32_t value) {
  return (value & NANO_RECORD_MASK) == NANO_RECORD_MAGIC && (value & 0xffu) <= 2u;
}
static inline bool nano_enter_dfu(uint8_t previous_stage, bool cold_power_on) {
  return cold_power_on && previous_stage == 2u;
}
static inline uint8_t nano_next_stage(uint8_t previous_stage) {
  return previous_stage < 2u ? previous_stage + 1u : 0u;
}
