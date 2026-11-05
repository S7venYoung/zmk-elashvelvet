"""Host-test actual patched connection/security callbacks; no radio or key writes."""
from pathlib import Path
import subprocess
import sys
import tempfile
from patch_split_security import patch

def function(source, name):
    start = source.index(name)
    at = source.index('{', start)
    depth = 1
    end = at + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]

source = Path(sys.argv[1]).read_text()
patched = patch(source)
assert patch(patched) == patched
prefix = '#include <assert.h>\n#include <errno.h>\n#include <stdbool.h>\n#include <stdint.h>\n#include <stddef.h>\n#define LOG_DBG(...) ((void)0)\n#define LOG_ERR(...) ((void)0)\n#define BT_SECURITY_L2 2\n#define BT_ATT_FIRST_ATTRIBUTE_HANDLE 1\n#define BT_ATT_LAST_ATTRIBUTE_HANDLE 65535\n#define BT_GATT_DISCOVER_PRIMARY 1\ntypedef int bt_security_t;\nenum bt_security_err { BT_SECURITY_ERR_SUCCESS, BT_SECURITY_ERR_AUTH_FAIL };\nstruct bt_conn { int security, request_error; };\nstruct peripheral_slot {struct bt_conn*conn;struct {unsigned value_handle;} subscribe_params;unsigned selected_physical_layout_handle;struct {void*uuid;void(*func)(void);unsigned start_handle,end_handle,type;} discover_params;};\nstatic struct peripheral_slot state;static bool present=true;static unsigned requested,discovered,layouts;\nstatic struct {int uuid;} split_service_uuid;\nstatic int update_peripherals_selected_layouts_work;\nstatic struct peripheral_slot*peripheral_slot_for_conn(struct bt_conn*c){(void)c;return present?&state:0;}\nstatic int bt_conn_get_security(struct bt_conn*c){return c->security;}\nstatic int bt_conn_set_security(struct bt_conn*c,int level){assert(level==2);requested++;return c->request_error;}\nstatic int bt_gatt_discover(struct bt_conn*c,void*p){(void)p;assert(c->security>=2);discovered++;return 0;}\nstatic void split_central_service_discovery_func(void){}\nstatic void k_work_submit(void*p){(void)p;layouts++;}\nstruct bt_conn_info {int unused;};\nstatic void bt_conn_get_info(struct bt_conn*c,struct bt_conn_info*i){(void)c;(void)i;}\nstatic int start_scanning(void){return 0;}\n'
main = 'int main(void){struct bt_conn c={.security=1};state.conn=&c;\n split_central_process_connection(&c);assert(requested==1&&discovered==0);\n c.security=2;split_central_security_changed(&c,2,BT_SECURITY_ERR_SUCCESS);assert(discovered==1&&layouts==0);\n state.subscribe_params.value_handle=10;state.selected_physical_layout_handle=40;\n split_central_security_changed(&c,2,BT_SECURITY_ERR_SUCCESS);assert(discovered==1&&layouts==1);\n split_central_security_changed(&c,2,BT_SECURITY_ERR_AUTH_FAIL);assert(discovered==1&&layouts==1);\n split_central_security_changed(&c,1,BT_SECURITY_ERR_SUCCESS);assert(discovered==1&&layouts==1);\n c.security=1;c.request_error=-EALREADY;split_central_process_connection(&c);assert(requested==2&&discovered==1);\n c.request_error=-EIO;split_central_process_connection(&c);assert(requested==3&&discovered==1);\n present=false;split_central_process_connection(&c);split_central_security_changed(&c,2,BT_SECURITY_ERR_SUCCESS);assert(requested==3&&discovered==1);\n return 0;}\n'
prefix = prefix.replace('static int start_scanning(void){return 0;}', 'static unsigned scans;\nstatic int start_scanning(void){scans++;return 0;}')
main = main.replace('requested==1&&discovered==0', 'requested==1&&discovered==0&&scans==1')
program = prefix + function(patched, 'static void split_central_process_connection(') + '\n' + function(patched, 'static void split_central_security_changed(') + main
with tempfile.TemporaryDirectory() as directory:
    cfile = Path(directory) / 'test.c'
    binary = Path(directory) / 'test'
    cfile.write_text(program)
    subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-fsanitize=address,undefined', str(cfile), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
print('Split security: encryption gate, first discovery, errors, existing handles and unrelated connections passed')
