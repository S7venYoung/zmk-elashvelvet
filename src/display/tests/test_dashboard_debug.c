#include <assert.h>
#include "../common/dashboard_debug.h"
int main(void) {
 uint8_t p[DASH_ACK_SIZE];
 dash_ack_encode(p,1,1,true,true,0x12345678,0xfedcba98);
 assert(dash_ack_valid(p,sizeof(p))&&p[1]==1&&p[2]==1&&p[3]==3);
 assert(dash_debug_u32(p+4)==0x12345678&&dash_debug_u32(p+8)==0xfedcba98);
 assert(!dash_ack_valid(p,sizeof(p)-1));
 p[1]=2;assert(!dash_ack_valid(p,sizeof(p)));p[1]=1;
 p[3]=4;assert(!dash_ack_valid(p,sizeof(p)));p[3]=1;
 p[2]=2;assert(!dash_ack_valid(p,sizeof(p)));p[2]=0;
 assert(dash_ack_valid(p,sizeof(p))); /* Cat is valid, missing left is irrelevant. */
 return 0;
}
