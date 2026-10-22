if(CONFIG_SHIELD_VELVET_CUBE_PERIPHERAL)
  zephyr_library_named(cube_identity)
  zephyr_library_sources(src/cube_identity.c)
endif()

if(CONFIG_VELVET_CUBE_SYSTEM_DISPLAY)
  target_sources(app PRIVATE src/display/cube_system_screen.c)
endif()

if(CONFIG_VELVET_CUBE_CAT_DISPLAY)
  target_sources(app PRIVATE src/display/themes/cat/cat_display.c)
endif()
