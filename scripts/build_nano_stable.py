#!/usr/bin/env python3
"""Build only the normal receiver using its complete matrix configuration."""
import json
from pathlib import Path
import shlex
import subprocess
import yaml

root = Path(__file__).resolve().parents[1]
target = next(t for t in yaml.safe_load((root / "build.yaml").read_text())["include"]
              if t.get("artifact") == "velvet_nano_dongle")
assert target["board"] == "nice_nano_k/nrf52833"
args = ["west", "build", "-s", str(root / "dependencies/zmk/app"),
        "-d", str(root / "build/nano_stable"), "-b", target["board"], "--",
        "-DZMK_CONFIG=" + str(root / "config"), "-DZMK_EXTRA_MODULES=" + str(root),
        "-DSHIELD=" + target["shield"], "-DSNIPPET=" + target["snippet"]]
args += shlex.split(target.get("cmake-args", ""))
print(json.dumps(args, indent=2), flush=True)
subprocess.run(args, cwd=root, check=True)
