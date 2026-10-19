if(CONFIG_VELVET_NANO_REPLUG_BOOTLOADER)
  target_sources(app PRIVATE src/nano_replug_bootloader.c)
endif()

if(CONFIG_VELVET_STUDIO_BINDING_ACTIONS)
  target_sources(app PRIVATE src/studio_binding_actions.c)
endif()

if(CONFIG_SHIELD_VELVET_NANO_DONGLE)
  zephyr_include_directories(${CMAKE_CURRENT_LIST_DIR}/src)
  target_sources(app PRIVATE src/velvet_stats.c src/scanner_payload.c)
endif()

if(CONFIG_SHIELD_VELVET_NANO_DONGLE OR CONFIG_SHIELD_VELVET_SPLIT_PERIPHERAL)
  zephyr_include_directories(${CMAKE_CURRENT_LIST_DIR}/src)
  target_sources(app PRIVATE src/half_telemetry.c)
endif()

# Each screen theme owns its source files and build rules.
add_subdirectory(src/display/themes/cat)
