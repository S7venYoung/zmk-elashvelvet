#include <stdbool.h>
#include <stdint.h>
#include "layout.h"

void select_image(void);
extern uint32_t selector_stack;

__attribute__((used, section(".vectors")))
static const uintptr_t vectors[] = {(uintptr_t)&selector_stack, (uintptr_t)select_image};

static bool bootable(uint32_t base, uint32_t limit) {
    const uint32_t *vector = (const uint32_t *)base;
    const uint32_t pc = vector[1] & ~1u;
    return vector[0] > 0x20000000u && vector[0] <= 0x20040000u &&
           (vector[0] & 7u) == 0 && (vector[1] & 1u) && pc >= base && pc < limit;
}

__attribute__((naked, noreturn))
static void jump(uint32_t base __attribute__((unused))) {
    __asm volatile("cpsid i\n"
                   "ldr r1, =0xe000ed08\n"
                   "str r0, [r1]\n"
                   "dsb\n"
                   "isb\n"
                   "ldmia r0, {r1, r2}\n"
                   "msr msp, r1\n"
                   "cpsie i\n"
                   "bx r2\n");
}

void select_image(void) {
    const uint32_t *mode = (const uint32_t *)VELVET_MODE_START;
    uint32_t selected = VELVET_MODE_NANO;
    for (unsigned i = 0; i < VELVET_PAGE_SIZE / sizeof(*mode) && mode[i] != UINT32_MAX; i++) {
        if (mode[i] == VELVET_MODE_NANO || mode[i] == VELVET_MODE_HOST) {
            selected = mode[i];
        }
    }
    if (selected == VELVET_MODE_HOST && bootable(VELVET_HOST_IMAGE_START, VELVET_HOST_SETTINGS_START)) {
        jump(VELVET_HOST_IMAGE_START);
    }
    if (bootable(VELVET_NANO_IMAGE_START, VELVET_HOST_IMAGE_START)) {
        jump(VELVET_NANO_IMAGE_START);
    }
    if (bootable(VELVET_HOST_IMAGE_START, VELVET_HOST_SETTINGS_START)) {
        jump(VELVET_HOST_IMAGE_START);
    }

    /* Neither image is usable. Ask the existing nice!nano bootloader for UF2. */
    *(volatile uint32_t *)0x4000051c = 0x57;
    __asm volatile("dsb");
    *(volatile uint32_t *)0xe000ed0c = 0x05fa0004;
    __asm volatile("dsb");
    for (;;) {}
}
