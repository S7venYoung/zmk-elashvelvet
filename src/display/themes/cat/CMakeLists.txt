# Current cat screen is right-only; the left uses ZMK's built-in screen.
if(CONFIG_VELVET_CAT_DISPLAY AND NOT CONFIG_VELVET_DASHBOARD_DISPLAY)
  target_sources(app PRIVATE ${CMAKE_CURRENT_LIST_DIR}/cat_display.c)
endif()

# Keep the existing layer relay compiled on the Nano receiver.
if(CONFIG_SHIELD_VELVET_NANO_DONGLE)
  target_sources(app PRIVATE ${CMAKE_CURRENT_LIST_DIR}/cat_layer_relay.c)
endif()
