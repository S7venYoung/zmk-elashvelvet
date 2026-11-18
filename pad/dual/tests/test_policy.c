#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "../policy.h"
int main(void) {
    assert(pad_crc32((const uint8_t *)"123456789", 9) == 0xcbf43926u);
    uint32_t words[8]; memset(words, 255, sizeof(words));
    assert(pad_read_mode(words, 8) == 0);
    words[0] = PAD_MODE_MAGIC | 1; /* Torn record must not select B. */
    assert(pad_read_mode(words, 8) == 0);
    words[1] = ~words[0]; assert(pad_read_mode(words, 8) == 1);
    words[2] = PAD_MODE_MAGIC; words[3] = ~words[2]; assert(pad_read_mode(words, 8) == 0);
    words[4] = 0x12345678; words[5] = ~words[4]; assert(pad_read_mode(words, 8) == 0);
    assert(pad_vector_valid(0x20040000, 0x28009, 0x28000, 0x29000));
    assert(!pad_vector_valid(0x20040004, 0x28009, 0x28000, 0x29000));
    assert(!pad_vector_valid(0x20040000, 0x27009, 0x28000, 0x29000));
    assert(!pad_vector_valid(0x20040000, 0x28008, 0x28000, 0x29000));
    assert(PAD_SLOT_A_LIMIT == PAD_SLOT_B_START && PAD_SLOT_B_LIMIT == PAD_SLOT_B_NVS);
    assert(PAD_SLOT_B_NVS + 0x8000 == PAD_BL_STAGING);
    assert(PAD_MODE_JOURNAL + PAD_PAGE_SIZE == PAD_SLOT_A_NVS);
    struct pad_chord_state chord = {0}; bool switched;
    assert(!pad_chord_event(&chord, 12, true, 0, &switched));
    assert(pad_chord_event(&chord, 10, true, 100, &switched));
    assert(!pad_chord_event(&chord, 12, false, 2200, &switched) && !switched);
    assert(pad_chord_event(&chord, 10, false, 2300, &switched) && switched);
    memset(&chord, 0, sizeof(chord));
    pad_chord_event(&chord, 12, true, 0, &switched);
    pad_chord_event(&chord, 10, true, 100, &switched);
    pad_chord_event(&chord, 10, false, 500, &switched);
    pad_chord_event(&chord, 12, false, 600, &switched); assert(!switched);
    memset(&chord, 0, sizeof(chord));
    pad_chord_event(&chord, 12, true, 0, &switched);
    pad_chord_event(&chord, 10, true, 100, &switched);
    pad_chord_event(&chord, 1, true, 2200, &switched);
    pad_chord_event(&chord, 1, false, 2300, &switched);
    pad_chord_event(&chord, 10, false, 2400, &switched);
    pad_chord_event(&chord, 12, false, 2500, &switched); assert(!switched);
    puts("Pad dual policy: CRC, torn records, mode replay, vector validation and partitions passed");
}
