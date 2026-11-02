from pathlib import Path
import json,re,unittest,uuid
ROOT=Path(__file__).resolve().parents[1]
class WebBootloaderTests(unittest.TestCase):
    def test_vendor_base_and_advertisement(self):
        definition=json.loads((ROOT/'bootloader/web-dfu.json').read_text())
        patch=(ROOT/'bootloader/eyelash-web-dfu.patch').read_text()
        data=bytes(int(x,16) for x in re.findall(r'0x([0-9A-F]{2})', '\n'.join(x for x in patch.splitlines() if x.startswith('+            '))))
        self.assertEqual(data,uuid.UUID(definition['base_uuid']).bytes[::-1])
        mk=(ROOT/'bootloader/boards/eyelash_numpad/board.mk').read_text()
        self.assertIn('-DEYELASH_WEB_DFU',mk);self.assertIn(definition['advertised_name'],mk)
        self.assertNotEqual(definition['service_uuid'],'00001530-1212-efde-1523-785feabcd123')
    def test_web_and_bootloader_uuid_contract(self):
        self.assertEqual(json.loads((ROOT/'web/web-dfu.json').read_text()),json.loads((ROOT/'bootloader/web-dfu.json').read_text()))
        core=(ROOT/'web/dfu-core.mjs').read_text()
        for name in ['service','control','packet']:
            self.assertIn(json.loads((ROOT/'bootloader/web-dfu.json').read_text())[name+'_uuid'],core)
    def test_patcher_and_release_include_contract(self):
        self.assertIn('eyelash-web-dfu.patch',(ROOT/'scripts/prepare_bootloader.py').read_text())
        self.assertIn('web_dfu',(ROOT/'scripts/firmware_artifacts.py').read_text())
