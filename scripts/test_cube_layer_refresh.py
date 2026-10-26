"""Source checks for LVGL queue ownership and the fast, bounded redraw cadence."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LayerRefreshTests(unittest.TestCase):
    def test_both_screens_poll_at_50ms(self):
        for path in ['src/display/themes/cat/cat_display.c',
                     'src/display/cube_system_screen.c']:
            source = (ROOT / path).read_text()
            self.assertIn('lv_timer_create(refresh,50,NULL)', source)

    def test_rendering_stays_on_lvgl_timer(self):
        cat = (ROOT / 'src/display/themes/cat/cat_display.c').read_text()
        receiver = cat[cat.index('static int receive_layer('):cat.index('ZMK_LISTENER(velvet_cat_layer')]
        self.assertNotIn('lv_obj_invalidate', receiver)
        self.assertNotIn('cat_render(', receiver)
        self.assertIn('current.layer==previous.layer', cat)
        system = (ROOT / 'src/display/cube_system_screen.c').read_text()
        receiver = system[system.index('static int on_event('):system.index('ZMK_LISTENER(velvet_dashboard')]
        self.assertNotIn('system_render(', receiver)
        self.assertNotIn('lv_obj_invalidate', receiver)
        self.assertIn('memcmp(&previous_view,&view,sizeof(view))', system)
        # Keep the original ~1Hz render heartbeat for DYA display diagnostics.
        self.assertIn('(uint32_t)(now-drawn_at)<1000u', system)


if __name__ == '__main__':
    unittest.main()
