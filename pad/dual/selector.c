/* SPDX-License-Identifier: MIT */
#include "policy.h"
extern uint32_t selector_stack;
void select_image(void);
__attribute__((naked, noreturn)) void selector_reset(void) { __asm volatile("cpsid i\nb select_image"); }
__attribute__((used, section(".vectors")))
static const uintptr_t vectors[] = {(uintptr_t)&selector_stack, (uintptr_t)selector_reset};
static bool usable(const struct pad_image_descriptor *d, unsigned mode) {
    uint32_t base = mode ? PAD_SLOT_B_START : PAD_SLOT_A_START;
    uint32_t limit = mode ? PAD_SLOT_B_LIMIT : PAD_SLOT_A_LIMIT;
    if (d->mode != mode || d->base != base || d->length < 8 || d->length > limit - base) return false;
    const uint32_t *v = (const uint32_t *)base;
    return pad_vector_valid(v[0], v[1], base, base + d->length) &&
           pad_crc32((const uint8_t *)base, d->length) == d->crc;
}
__attribute__((naked, noreturn)) static void jump(uint32_t base __attribute__((unused))) {
    __asm volatile("cpsid i\n"
                   "ldr r1, =0xe000e010\nmovs r2, #0\nstr r2, [r1]\n"
                   "ldr r1, =0xe000ed04\nldr r2, =0x0a000000\nstr r2, [r1]\n"
                   "ldr r1, =0xe000e180\nldr r2, =0xffffffff\nstr r2, [r1]\nstr r2, [r1, #4]\n"
                   "ldr r1, =0xe000e280\nstr r2, [r1]\nstr r2, [r1, #4]\n"
                   "ldr r1, =0xe000ed08\nstr r0, [r1]\ndsb\nisb\n"
                   "movs r3, #0\nmsr control, r3\nmsr basepri, r3\nmsr faultmask, r3\nisb\n"
                   "ldmia r0, {r1, r2}\nmsr msp, r1\n"
                   "ldr r3, =0xffffffff\nmov lr, r3\nbx r2\n");
}
void select_image(void) {
    const struct pad_image_table *table = (const void *)PAD_SELECTOR_META;
    if (table->magic == PAD_META_MAGIC && table->version == 1 && table->count == 2) {
        unsigned mode = pad_read_mode((const void *)PAD_MODE_JOURNAL, PAD_PAGE_SIZE / 4);
        if (usable(&table->image[mode], mode)) jump(table->image[mode].base);
        if (usable(&table->image[mode ^ 1u], mode ^ 1u)) jump(table->image[mode ^ 1u].base);
    }
    *(volatile uint32_t *)0x4000051c = 0x57; /* Existing Rasi UF2 entry. */
    __asm volatile("dsb");
    *(volatile uint32_t *)0xe000ed0c = 0x05fa0004;
    __asm volatile("dsb");
    for (;;) {}
}
