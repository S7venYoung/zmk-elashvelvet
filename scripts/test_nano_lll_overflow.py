#!/usr/bin/env python3
"""Exercise the exact injected overflow branch with a mock role abort callback."""
from pathlib import Path
import subprocess
import sys
import tempfile

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    source = root / "lll.c"
    source.write_text(Path(sys.argv[1]).read_text())
    patcher = Path(__file__).with_name("patch_nano_lll_overflow.py")
    subprocess.run([sys.executable, str(patcher), str(source)], check=True)
    patched = source.read_text()
    subprocess.run([sys.executable, str(patcher), str(source)], check=True)
    assert patched == source.read_text()
    start = patched.index("\t\tif (!next && !is_resume && !is_dequeue &&")
    end = patched.index("\t\tLL_ASSERT(next);", start)
    block = patched[start:end]
    harness = r"""
#include <assert.h>
#include <stdint.h>
#include <stddef.h>
#define IS_ENABLED(x) (x)
static volatile uint32_t velvet_lll_prepare_overflows;
struct prep { void *param; };
static int aborts;
static struct prep *observed;
static void *observed_param;
static void abort_cb(struct prep *prepare, void *param) {
    aborts++;
    observed = prepare;
    observed_param = param;
}
"""
    function = """
static int contain(void *next, int is_resume, int is_dequeue,
                   struct prep *prepare_param) {
""" + block + """
    return 123;
}
"""
    tests = r"""
int main(void) {
    int role;
    struct prep prepare = { &role };
    int result = contain(NULL, 0, 0, &prepare);
    if (CONFIG_BT_CTLR_LOW_LAT) {
        assert(result == 123 && aborts == 0 && velvet_lll_prepare_overflows == 0);
    } else {
        assert(result == 0 && aborts == 1 && velvet_lll_prepare_overflows == 1);
        assert(observed == &prepare && observed_param == &role);
    }
    int count = aborts;
    assert(contain(&role, 0, 0, &prepare) == 123);
    assert(contain(NULL, 1, 0, &prepare) == 123);
    assert(contain(NULL, 0, 1, &prepare) == 123);
    assert(aborts == count);
}
"""
    c = root / "test.c"
    c.write_text(harness + function + tests)
    for low_lat in (0, 1):
        binary = root / f"test-{low_lat}"
        subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                        f"-DCONFIG_BT_CTLR_LOW_LAT={low_lat}",
                        "-DCONFIG_SHIELD_VELVET_NANO_DONGLE=1", str(c), "-o", str(binary)],
                       check=True)
        subprocess.run([str(binary)], check=True)
print("Fresh overflow cleanup, resumed/dequeued events and low latency guards passed")
