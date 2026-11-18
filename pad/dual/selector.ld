ENTRY(selector_reset)
MEMORY { FLASH (rx) : ORIGIN = 0x27000, LENGTH = 0xf00 }
selector_stack = 0x20040000;
SECTIONS {
 .text : { KEEP(*(.vectors)) *(.text*) *(.rodata*) } > FLASH
 /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.note*) *(.comment*) }
}
