#!/usr/bin/env python3
"""Contain a fresh radio prepare overflow in the Nordic split receiver controller."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text()
marker = "/* VELVET_LLL_PREPARE_OVERFLOW */"
if marker in source:
    sys.exit(0)
anchor = """		next = ull_prepare_enqueue(is_abort_cb, abort_cb, prepare_param,
					   prepare_cb, is_resume);
		LL_ASSERT(next);"""
if source.count(anchor) != 1:
    sys.exit("Unexpected Nordic LLL prepare queue code")
source = source.replace("int lll_prepare_resolve(lll_is_abort_cb_t", marker + """
/* LLL context writes; the diagnostic snapshot only reads this aligned word. */
volatile uint32_t velvet_lll_prepare_overflows;

int lll_prepare_resolve(lll_is_abort_cb_t""", 1)
source = source.replace(anchor, anchor.replace("		LL_ASSERT(next);", """		if (!next && !is_resume && !is_dequeue &&
		    !IS_ENABLED(CONFIG_BT_CTLR_LOW_LAT)) {
			/* Cancel a fresh prepare using the role's normal cleanup.
			 * This releases its clock/ref via lll_done, so a full
			 * pipeline does not leave the event permanently pending.
			 * Resumes keep the original invariant check below.
			 */
			velvet_lll_prepare_overflows++;
			abort_cb(prepare_param, prepare_param->param);
			return 0;
		}
		LL_ASSERT(next);"""))
path.write_text(source)
