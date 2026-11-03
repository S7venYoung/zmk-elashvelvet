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

if(CONFIG_VELVET_DASHBOARD_DISPLAY)
  target_sources(app PRIVATE src/display/dashboard_screen.c)
endif()
if(CONFIG_SHIELD_VELVET_NANO_DONGLE)
  target_sources(app PRIVATE src/display/dashboard_bridge.c)
endif()
target_sources_ifdef(CONFIG_ZMK_BEHAVIOR_EYELASH_DFU app PRIVATE src/behavior_eyelash_dfu.c)

target_sources_ifdef(CONFIG_VELVET_PAD_LINK_DIAGNOSTICS app PRIVATE src/pad_link_diagnostics.c)

# Local recovery must run on the Pad, even without a split connection.
if(CONFIG_SHIELD_EYELASH_NUMPAD AND CONFIG_SOC_NRF52832_QFAA)
  target_sources(app PRIVATE src/eyelash_local_dfu.c)
endif()
