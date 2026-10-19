/* SPDX-License-Identifier: MIT */
#pragma once
#include "pixels.h"
#include "dashboard_data.h"
static inline void panel_header(uint8_t*p,struct panel_status s){
 char n[8];outline(p,2,3,14,8);
 for(int i=0;i<4;i++){box(p,4+3*i,5,1,1,false);box(p,4+3*i,7,1,1,false);}box(p,5,9,8,1,false);
 n[0]=s.side;n[1]=0;text(p,21,4,n,1);box(p,31,2,1,10,false);
 /* BLE rune and a binary link indicator, not measured RSSI. */
 box(p,39,1,1,11,false);
 for(int i=0;i<5;i++){px(p,39+i,1+i,false);px(p,43-i,5+i,false);px(p,36+i,3+i,false);px(p,36+i,9-i,false);}
 if(s.connected)for(int i=0;i<3;i++)box(p,49+3*i,9-2*i,2,2+2*i,false);
 else outline(p,49,6,8,5);
 box(p,63,2,1,10,false);
 /* USB plug icon plus actual dongle transport label. */
 outline(p,73,1,6,6);box(p,74,2,1,2,false);box(p,77,2,1,2,false);outline(p,71,7,10,5);
 box(p,73,9,2,1,false);box(p,77,9,2,1,false);text(p,86,4,"USB",1);box(p,107,2,1,10,false);
 outline(p,113,3,15,8);box(p,128,5,2,4,false);
 if(s.battery_valid)for(int i=0;i<4;i++)if(s.battery>i*25)box(p,115+3*i,5,2,4,false);
 if(s.battery_valid)snprintf(n,sizeof(n),"%u%%",s.battery);else strcpy(n,"--%");
 text(p,133,4,n,1);box(p,1,14,158,1,false);
}
static inline void panel_layer(uint8_t*p,int x,int y,struct panel_status s){
 char n[8];outline(p,x,y,37,13);
 if(s.layer_valid&&s.layer>=99){tiny_text(p,x+3,y+4,"LYR");snprintf(n,sizeof(n),"%u",(unsigned)s.layer+1);tiny_text(p,x+19,y+4,n);return;}
 /* Hand-spaced four-column LAYER word, seven pixels high. */
 static const uint8_t label[5][4]={{0x7f,0x40,0x40,0x40},{0x7e,9,9,0x7e},{3,4,0x7c,3},{0x7f,0x49,0x49,0x41},{0x7f,9,0x19,0x66}};
 for(unsigned c=0;c<5;c++)for(unsigned col=0;col<4;col++)for(unsigned row=0;row<7;row++)
 if(label[c][col]&(1u<<row))px(p,x+3+(int)c*5+(int)col,y+3+(int)row,false);
 if(s.layer_valid)snprintf(n,sizeof(n),"%u",(unsigned)s.layer+1);else strcpy(n,"--");
 tiny_text(p,x+29,y+4,n);
}
