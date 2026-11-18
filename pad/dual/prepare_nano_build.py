"""Keep the established Nano board, snippet and CMake tuning, build no halves."""
from pathlib import Path
import yaml
p=Path('build.yaml');data=yaml.safe_load(p.read_text())
selected=[x for x in data['include'] if x.get('artifact')=='velvet_nano_dongle']
assert len(selected)==1 and selected[0]['board']=='nice_nano_k/nrf52833'
p.write_text(yaml.safe_dump({'include':selected},sort_keys=False))
