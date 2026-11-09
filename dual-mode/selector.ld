ENTRY(select_image)
MEMORY {
    FLASH (rx) : ORIGIN = 0x26000, LENGTH = 4K
}
selector_stack = 0x20040000;
SECTIONS {
    .text : {
        KEEP(*(.vectors))
        *(.text*)
        *(.rodata*)
    } > FLASH
    /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.note*) *(.comment*) }
}
