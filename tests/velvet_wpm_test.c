#include "../src/velvet_wpm.h"
#include <assert.h>
int main(void) {
    unsigned left=0,right=0;
    for(unsigned i=0;i<61;i++) { if(velvet_position_side(i)==0)left++;else right++; }
    assert(left==32 && right==29 && velvet_position_side(61)==-1);
    assert(velvet_position_side(6)==1 && velvet_position_side(18)==0 && velvet_position_side(19)==1);
    struct velvet_history h[2]={0};
    velvet_record(&h[0],100);
    assert(velvet_wpm(&h[0],100)==2 && velvet_wpm(&h[1],100)==0);
    assert(velvet_wpm(&h[0],5100)==2 && velvet_wpm(&h[0],5101)==0);
    for(unsigned i=0;i<150;i++)velvet_record(&h[1],1000+i);
    assert(velvet_wpm(&h[1],1200)==255);
    struct velvet_history wrap={0}; velvet_record(&wrap,UINT32_MAX-100);
    assert(velvet_wpm(&wrap,100)==2 && velvet_wpm(&wrap,6000)==0);
}
