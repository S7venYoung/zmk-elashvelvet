/* SPDX-License-Identifier: MIT */
#pragma once
#include "../../common/header.h"
static inline void system_render(uint8_t*p,const struct dashboard_status*s){
 memset(p,255,PANEL_BYTES);panel_header(p,s->keyboard);
 char n[24];text(p,3,21,"CPU",1);
 if(s->data[1]&DASH_CPU)snprintf(n,sizeof(n),"%u%%",s->data[3]);else strcpy(n,"--%");text(p,3,32,n,2);
 /* Temperature has its own validity bit. Never substitute CPU usage. */
 if(s->data[1]&DASH_TEMP){int v=(int16_t)dash_u16(s->data+8);snprintf(n,sizeof(n),"%s%d.%d",v<0?"-":"",v<0?-(v/10):v/10,v<0?-(v%10):v%10);}else strcpy(n,"--");
 text(p,3,55,n,1);int end=3+(int)strlen(n)*6;outline(p,end,53,3,3);text(p,end+5,55,"C",1);
 for(unsigned i=0;i<s->count&&i<12;i++){int h=s->history[i]>100?100:s->history[i];h=h*30/100;
 box(p,51+(int)i*2,64-h,1,h,false);}
 box(p,78,21,1,45,false);text(p,83,21,"RAM",1);
 if(s->data[1]&DASH_RAM){unsigned used=(unsigned)dash_u16(s->data+10)*64,total=(unsigned)dash_u16(s->data+12)*64;
 unsigned tenth=(used*10+512)/1024;snprintf(n,sizeof(n),"%u.%u/%uG",tenth/10,tenth%10,total/1024);}else strcpy(n,"--/--G");text(p,83,32,n,1);
 if(s->data[1]&DASH_RAM)snprintf(n,sizeof(n),"%u%%",s->data[4]);else strcpy(n,"--%");text(p,83,43,n,1);
 bar(p,83,55,37,10,s->data[4],s->data[1]&DASH_RAM);panel_layer(p,122,53,s->keyboard);
}
