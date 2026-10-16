/* SPDX-License-Identifier: MIT */
#include <assert.h>
enum { BT_LE_ADV_OPT_FORCE_NAME_IN_AD = 1 << 18, BT_LE_ADV_OPT_SCANNABLE = 1 << 9 };
#if defined(BT_LE_ADV_OPT_FORCE_NAME_IN_AD)
#define OLD_FORCE_BRANCH 1
#else
#define OLD_FORCE_BRANCH 0
#endif
int main(void) {
    assert(OLD_FORCE_BRANCH == 0); /* Reproduce the enum-vs-macro error. */
    assert(BT_LE_ADV_OPT_FORCE_NAME_IN_AD != 0);
    assert(BT_LE_ADV_OPT_SCANNABLE != 0);
    const unsigned standard_payload = 26, fight_payload = 17;
    const unsigned flags = 3, manufacturer_header = 2, complete_name = 2 + 8;
    assert(flags + manufacturer_header + standard_payload == 31);
    assert(complete_name <= 31); /* Separate scan response holds Velvet46. */
    assert(manufacturer_header + standard_payload <= 31); /* Piggyback SD. */
    assert(flags + complete_name <= 31); /* Name in AD, status in SD. */
    assert(flags + manufacturer_header + standard_payload + complete_name > 31);
    assert(flags + manufacturer_header + fight_payload + complete_name == 32);
    return 0;
}
