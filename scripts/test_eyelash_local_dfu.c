#include <assert.h>
#include "eyelash_local_dfu.h"
int main(void) {
 struct eyelash_dfu_hold s = {0};
 assert(!eyelash_dfu_update(&s,61,true,0));
 assert(!eyelash_dfu_due(&s,5000));
 assert(eyelash_dfu_update(&s,63,true,5000)==1);
 assert(!eyelash_dfu_due(&s,7999));
 assert(eyelash_dfu_due(&s,8000));
 assert(eyelash_dfu_update(&s,61,false,8001)==-1);
 assert(!eyelash_dfu_due(&s,9000));
 assert(eyelash_dfu_update(&s,61,true,9000)==1);
 assert(!eyelash_dfu_due(&s,10000));
 assert(!eyelash_dfu_update(&s,61,true,10000));
 assert(eyelash_dfu_due(&s,12000));
 assert(eyelash_dfu_update(&s,63,false,12001)==-1);
 assert(!eyelash_dfu_due(&s,20000));
 return 0;
}
