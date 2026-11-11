#!/usr/bin/env python3
"""Port ZMK PR #3538 to the DYA split central for a diagnostic comparison."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text()
marker = "/* ZMK upstream PR #3538 */"
if marker in source:
    sys.exit(0)
if "VELVET_NANO_SPLIT_SCAN_RECOVERY" in source:
    sys.exit("PR #3538 must run without the local Nano scan recovery patch")

definition = "static int start_scanning(void) {"
failure = '        LOG_ERR("Scanning failed to start (err %d)", err);\n        return err;'
for anchor in ("static int start_scanning(void);", definition, failure):
    if source.count(anchor) != 1:
        sys.exit(f"Unexpected ZMK scan source: {anchor}")
source = source.replace(definition, marker + """
static void start_scanning_retry_fn(struct k_work *work) {
    ARG_UNUSED(work);
    start_scanning();
}

static K_WORK_DELAYABLE_DEFINE(start_scanning_retry, start_scanning_retry_fn);

""" + definition)
source = source.replace(failure, failure.replace("        return err;",
    "        is_scanning = false;\n"
    "        k_work_reschedule(&start_scanning_retry, K_SECONDS(1));\n"
    "        return err;"))
path.write_text(source)
