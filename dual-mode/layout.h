/* nice!nano nRF52840 application flash, below the existing settings partition. */
#define VELVET_SELECTOR_START 0x26000
#define VELVET_NANO_IMAGE_START 0x27000
#define VELVET_HOST_IMAGE_START 0x82000
#define VELVET_HOST_SETTINGS_START 0xe7000
/* Both right-hand apps and the boot selector share this single flash page. */
#define VELVET_MODE_START 0xeb000
#define VELVET_SETTINGS_START 0xec000
#define VELVET_MODE_NANO 0x4e414e4f
#define VELVET_MODE_HOST 0x484f5354
#define VELVET_PAGE_SIZE 0x1000

#if (VELVET_MODE_START % VELVET_PAGE_SIZE) != 0 || \
    (VELVET_MODE_START + VELVET_PAGE_SIZE) != VELVET_SETTINGS_START || \
    VELVET_HOST_SETTINGS_START >= VELVET_MODE_START
#error "The shared mode page must be aligned and separate from both NVS areas"
#endif
