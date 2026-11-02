#!/usr/bin/env python3
"""Host checks for the append-only Velvet + numpad split configuration."""
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASELINE = json.loads((ROOT / "tests/numpad_baseline.json").read_text())


def without_comments(text):
    return re.sub(r"//[^\n]*|/\*.*?\*/", "", text, flags=re.S)


def keymap_layers():
    text = (ROOT / "config/velvet.keymap").read_text()
    text = text[text.index("    keymap {"):]
    result = []
    for body in re.findall(r"bindings\s*=\s*<(.*?)>;", text, re.S):
        result.append([" ".join(binding.split()) for binding in
                       re.findall(r"&[A-Za-z0-9_]+[^&]*", without_comments(body))])
    return result


class NumpadTests(unittest.TestCase):
    def test_append_only_transform(self):
        text = (ROOT / "boards/shields/velvet/velvet-numpad-transform.dtsi").read_text()
        positions = [list(map(int, pair)) for pair in re.findall(
            r"RC\(\s*(\d+)\s*,\s*(\d+)\s*\)", text)]
        self.assertEqual(positions[:61], BASELINE["matrix"])
        self.assertEqual(positions[61:], [[r, c] for r in range(5, 9) for c in range(4)])
        self.assertEqual(len({tuple(p) for p in positions}), 77)
        self.assertLessEqual(len(positions), 16 * 8)  # split protocol's 16-byte bitmap
        for path in ("velvet.dtsi", "velvet_nano_dongle.overlay"):
            self.assertIn('"velvet-numpad-transform.dtsi"',
                          (ROOT / "boards/shields/velvet" / path).read_text())

    def test_layout_keeps_original_coordinates(self):
        text = (ROOT / "boards/shields/velvet/velvet-layouts.dtsi").read_text()
        attrs = [" ".join(x.split()) for x in re.findall(r"<&key_physical_attrs\s+([^>]+)>", text)]
        self.assertEqual(attrs[:61], BASELINE["physical"])
        self.assertEqual(len(attrs), 77)
        self.assertEqual([list(map(int, x.split())) for x in attrs[61:]],
                         [[100, 100, 2100 + c * 100, r * 100, 0, 0, 0]
                          for r in range(4) for c in range(4)])

    def test_existing_bindings_except_removed_password_are_unchanged(self):
        layers = keymap_layers()
        self.assertEqual([len(layer) for layer in layers], [77] * 4)
        for index in range(3):
            digest = hashlib.sha256(json.dumps(layers[index][:61]).encode()).hexdigest()
            self.assertEqual(digest, BASELINE["bindings_sha256"][index])
        text = (ROOT / "config/velvet.keymap").read_text()
        self.assertNotIn("pwd_enter", text)
        self.assertNotRegex(text, r"\bmacros\s*\{")

    def test_numpad_stays_numeric_on_all_original_layers(self):
        layers = keymap_layers()
        for layer in layers[1:3]:
            self.assertEqual(layer[61:], layers[0][61:])
        self.assertEqual(layers[0][73], "&lt NUMPAD_FN KP_ENTER")
        self.assertEqual(layers[0][61:65], ["&kp KP_N7", "&kp KP_N8", "&kp KP_N9", "&kp KP_DIVIDE"])
        self.assertEqual(layers[3][:61], ["&trans"] * 61)
        self.assertEqual(layers[3][76], "&eyelash_dfu")
        # Adding numpad Fn never changes the effective binding of a Velvet key.
        def resolve(position, active):
            for index in reversed(active):
                if layers[index][position] != "&trans":
                    return layers[index][position]
            return "&none"
        for active in ([0], [0, 1], [0, 2], [0, 1, 2]):
            for position in range(61):
                self.assertEqual(resolve(position, active), resolve(position, list(active) + [3]))

    def test_numpad_offset_and_lightweight_role(self):
        text = (ROOT / "boards/eyelash/eyelash_numpad/eyelash_numpad_nrf52832.dts").read_text()
        self.assertIn("row-offset = <5>", text)
        self.assertIn("zmk,physical-layout = &velvet_layout", text)
        self.assertNotIn("zmk,matrix-transform =", text)
        cfg = (ROOT / "config/eyelash_numpad.conf").read_text()
        self.assertIn("CONFIG_ZMK_SPLIT_ROLE_CENTRAL=n", cfg)
        for name in ("ZMK_STUDIO", "ZMK_RUNTIME_MACRO", "ZMK_RUNTIME_TAPDANCE",
                     "ZMK_RUNTIME_COMBO", "ZMK_DISPLAY", "ZMK_POINTING"):
            self.assertIn(f"CONFIG_{name}=n", cfg)
        peripheral = (ROOT / "config/eyelash_numpad.keymap").read_text()
        self.assertEqual(peripheral.count("&none"), 77)

    def test_connection_budget_and_no_automatic_build(self):
        cfg = (ROOT / "boards/shields/velvet/velvet_nano_dongle.conf").read_text()
        for name, value in (("ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS", 3), ("BT_MAX_CONN", 4),
                            ("BT_MAX_PAIRED", 8), ("PROSPECTOR_EXPECTED_PERIPHERAL_COUNT", 3)):
            self.assertRegex(cfg, rf"(?m)^CONFIG_{name}={value}$")
        for path in (ROOT / ".github/workflows").glob("*.yml"):
            text = path.read_text()
            self.assertIn("workflow_dispatch:", text)
            self.assertNotRegex(text, r"(?m)^\s+(push|pull_request):")


if __name__ == "__main__":
    unittest.main(verbosity=2)
