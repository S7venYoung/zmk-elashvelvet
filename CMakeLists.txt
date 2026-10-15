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
