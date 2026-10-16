/* SPDX-License-Identifier: MIT */
#pragma once
#include <stddef.h>
#include <stdint.h>

/* Alternate two legacy packets on the same identity/advertiser. */
const uint8_t *velvet_scanner_payload(const uint8_t *status, size_t status_size,
                                     const uint8_t keyboard_id[4], size_t *size);
