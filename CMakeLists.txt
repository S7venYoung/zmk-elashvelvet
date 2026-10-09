if(CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
  zephyr_library()
  zephyr_library_sources(src/velvet_stats.c src/fight_telemetry.c)
endif()
