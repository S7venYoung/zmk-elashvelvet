"""Install the Nano-only action hook in the fetched ZMK keymap setter."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text()
marker = "/* Velvet Nano Studio action hook */"
if marker in source:
    raise SystemExit("Studio action hook already installed; refusing duplicate patch")
include = "#include <zmk/keymap.h>"
anchor = "    if (memcmp(&zmk_keymap[layer_id][storage_binding_idx], &binding, sizeof(binding)) == 0) {"
if source.count(include) != 1 or source.count(anchor) != 1:
    raise SystemExit("ZMK keymap setter changed; inspect upstream before applying hook")
source = source.replace(include, include + "\n#if IS_ENABLED(CONFIG_VELVET_STUDIO_BINDING_ACTIONS)\nint velvet_studio_binding_action(const struct zmk_behavior_binding *binding);\n#endif", 1)
source = source.replace(anchor, marker + "\n#if IS_ENABLED(CONFIG_VELVET_STUDIO_BINDING_ACTIONS)\n    int action = velvet_studio_binding_action(&binding);\n    if (action != 0) {\n        return action < 0 ? action : 0;\n    }\n#endif\n\n" + anchor, 1)
path.write_text(source)
print(f"Installed Studio binding action hook: {path}")
