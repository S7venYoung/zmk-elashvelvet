if(CONFIG_VELVET_NANO_REPLUG_BOOTLOADER)
  target_sources(app PRIVATE src/nano_replug_bootloader.c)
endif()

if(CONFIG_VELVET_STUDIO_BINDING_ACTIONS)
  target_sources(app PRIVATE src/studio_binding_actions.c)
endif()

# Only the dongle advertises; keyboard peripherals keep their existing firmware.
if(CONFIG_SHIELD_VELVET_NANO_DONGLE)
  target_sources(app PRIVATE src/velvet_stats.c src/fight_telemetry.c)
endif()

if(CONFIG_SHIELD_VELVET_NANO_DONGLE OR CONFIG_SHIELD_VELVET_SPLIT_PERIPHERAL)
  zephyr_include_directories(${CMAKE_CURRENT_LIST_DIR}/src)
  target_sources(app PRIVATE src/half_telemetry.c)
endif()
