/* SPDX-License-Identifier: MIT */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "cat_frame.h"
#include "cat_layer.h"

int main(int argc,char **argv) {
    struct { uint8_t before[16],frame[CAT_FRAME_BYTES],after[16]; } b;
    memset(&b,0xa5,sizeof(b));
    for (int connected=0;connected<2;++connected)
        for (unsigned battery=0;battery<=101;++battery)
            for (unsigned layer=0;layer<255;++layer) {
                struct cat_status s={.connected=connected,.battery_valid=battery<=100,
                    .battery=battery,.layer_valid=true,.layer=layer};
                cat_render(b.frame,s);
                for (unsigned i=0;i<16;++i) assert(b.before[i]==0xa5 && b.after[i]==0xa5);
            }
    uint8_t previous[CAT_FRAME_BYTES];
    struct cat_status s={.connected=true,.battery_valid=true,.battery=0,.layer_valid=true};
    cat_render(previous,s);
    s.battery=100;cat_render(b.frame,s);assert(memcmp(previous,b.frame,sizeof(previous)));
    s.battery_valid=false;cat_render(previous,s);assert(memcmp(previous,b.frame,sizeof(previous)));
    struct cat_layer_sample layer={0};
    const uint8_t valid[]={1,31},bad_version[]={2,1},invalid[]={1,255};
    assert(!cat_layer_live(&layer,0));
    assert(!cat_layer_accept(&layer,NULL,2,0));
    assert(!cat_layer_accept(&layer,valid,1,0));
    assert(!cat_layer_accept(&layer,bad_version,2,0));
    assert(!cat_layer_accept(&layer,invalid,2,0));
    assert(cat_layer_accept(&layer,valid,2,0xfffffff0));
    assert(layer.layer==31 && cat_layer_live(&layer,0x10));
    assert(cat_layer_live(&layer,(uint32_t)(0xfffffff0u+4999)));
    assert(!cat_layer_live(&layer,(uint32_t)(0xfffffff0u+5000)));
    if(argc>1) {
        s=(struct cat_status){.connected=true,.battery_valid=true,.battery=86,
                              .layer_valid=true,.layer=0};
        cat_render(b.frame,s);
        FILE *f=fopen(argv[1],"wb");assert(f);
        fprintf(f,"P4\n160 68\n");assert(fwrite(b.frame,1,sizeof(b.frame),f)==sizeof(b.frame));
        fclose(f);
    }
    puts("Cat display: render boundaries, zero/unknown battery, malformed layer packets and expiry passed");
    return 0;
}
