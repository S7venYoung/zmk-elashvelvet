if(CONFIG_SHIELD_VELVET_CUBE_PERIPHERAL)
  zephyr_library_named(cube_identity)
  zephyr_library_sources(src/cube_identity.c)
endif()
