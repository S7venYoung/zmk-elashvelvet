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

# Right-only custom screen; left keeps its existing built-in display.
if(CONFIG_VELVET_CAT_DISPLAY)
  target_sources(app PRIVATE src/cat_display.c)
endif()
if(CONFIG_SHIELD_VELVET_NANO_DONGLE)
  target_sources(app PRIVATE src/cat_layer_relay.c)
endif()
