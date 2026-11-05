"""Gate Nano split discovery on encryption; preserve all bonds and handles."""
from pathlib import Path
import sys
MARKER = 'VELVET_SPLIT_SECURITY_GATE'
GUARD = '''    /* VELVET_SPLIT_SECURITY_GATE: encrypted CCCs must not be subscribed before
     * the link is secure. Existing bonds are reused; never erase them here. */
    if (bt_conn_get_security(conn) < BT_SECURITY_L2) {
        err = bt_conn_set_security(conn, BT_SECURITY_L2);
        if (err < 0 && err != -EALREADY) {
            LOG_ERR("Split link security request failed (%d)", err);
        }
        /* Do not block discovery of the other half while security is pending. */
        start_scanning();
        return;
    }

'''

def patch(source):
    if MARKER in source:
        return source
    begin = source.index('static void split_central_process_connection(struct bt_conn *conn) {')
    end = source.index('static int start_scanning', begin) if 'static int start_scanning' in source[begin:] else len(source)
    part = source[begin:end]
    anchor = '    if (!slot->subscribe_params.value_handle) {'
    if part.count(anchor) != 1:
        raise ValueError('Unexpected split discovery entry')
    part = part.replace(anchor, GUARD + anchor, 1)
    source = source[:begin] + part + source[end:]
    begin = source.index('static void split_central_security_changed(')
    end = source.index('static struct bt_conn_cb conn_callbacks', begin)
    part = source[begin:end]
    old = 'if (!slot || !slot->selected_physical_layout_handle) {'
    if part.count(old) != 1:
        raise ValueError('Unexpected split security callback guard')
    part = part.replace(old, 'if (!slot) {', 1)
    anchor = '    k_work_submit(&update_peripherals_selected_layouts_work);'
    if part.count(anchor) != 1:
        raise ValueError('Unexpected split security callback completion')
    part = part.replace(anchor, '''    /* A successful security event also resumes first-time discovery, when
     * no layout handle can exist yet. Existing subscriptions stay intact. */
    split_central_process_connection(conn);
    if (slot->selected_physical_layout_handle) {
        k_work_submit(&update_peripherals_selected_layouts_work);
    }''', 1)
    return source[:begin] + part + source[end:]

if __name__ == '__main__':
    p = Path(sys.argv[1]);p.write_text(patch(p.read_text()))
