#!/usr/bin/env python3
"""Exercise the actual Zephyr command encoder with/without serial VCOM."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

source = Path(sys.argv[1]).read_text()
match = re.search(r"static int ls0xx_cmd\([^\n]*\)\n\{.*?^\}", source, re.M | re.S)
if not match:
    raise SystemExit("Unexpected LS0XX command encoder structure")
function = match.group(0)
prefix = r"""
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <assert.h>
#ifndef SERIAL_VCOM
#error Test must choose serial VCOM mode
#endif
#define DT_INST_PROP(inst, prop) SERIAL_VCOM
#define LS0XX_BIT_VCOM 0x02
#define LOG_ERR(...) ((void)0)
struct spi_buf {void *buf; size_t len;};
struct spi_buf_set {const struct spi_buf *buffers; size_t count;};
struct ls0xx_config {int bus;};
struct ls0xx_data {bool vcom_state;};
struct device {const void *config; void *data;};
static unsigned sent;
static uint8_t commands[4];
static int spi_write_dt(const int *bus,const struct spi_buf_set *set) {
    (void)bus; assert(set->count==1 && sent<4);
    commands[sent++]=((const uint8_t *)set->buffers[0].buf)[0];
    return 0;
}
"""
suffix = r"""
int main(void) {
    const struct ls0xx_config config={0};
    struct ls0xx_data data={0};
    const struct device dev={.config=&config,.data=&data};
    for(unsigned i=0;i<4;++i) {
        uint8_t idle[2]={0};
        assert(ls0xx_cmd(&dev,idle,sizeof(idle))==0);
        assert(commands[i]==(SERIAL_VCOM && (i&1)?LS0XX_BIT_VCOM:0));
    }
    return 0;
}
"""
with tempfile.TemporaryDirectory() as tmp:
    c = Path(tmp)/"test.c"
    c.write_text(prefix+function+suffix)
    for mode in (0,1):
        binary=Path(tmp)/("test-"+str(mode))
        subprocess.run(["cc","-std=c11","-Wall","-Wextra","-Werror",
                        "-DSERIAL_VCOM="+str(mode),str(c),"-o",str(binary)],check=True)
        subprocess.run([str(binary)],check=True)
print("LS0XX: missing VCOM produces constant polarity; enabled VCOM alternates idle commands")
