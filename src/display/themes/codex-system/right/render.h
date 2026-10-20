/* SPDX-License-Identifier: MIT */
#pragma once
#include "../../../common/header.h"
static inline void system_render(uint8_t*p,const struct dashboard_status*s){
 memset(p,255,PANEL_BYTES);panel_header(p,s->keyboard);char n[24];const uint8_t flags=s->data[1];
 text(p,3,23,"CPU",1);solid_bar(p,38,21,82,10,s->data[3],flags&DASH_CPU);
 if(flags&DASH_CPU)snprintf(n,sizeof(n),"%u%%",s->data[3]);else strcpy(n,"--%");text(p,127,23,n,1);
 text(p,3,40,"RAM",1);solid_bar(p,38,38,82,10,s->data[4],flags&DASH_RAM);
 if(flags&DASH_RAM)snprintf(n,sizeof(n),"%u%%",s->data[4]);else strcpy(n,"--%");text(p,127,40,n,1);
 int temperature=0;unsigned fill=0;
 if(flags&DASH_TEMP){int v=(int16_t)dash_u16(s->data+8);temperature=v>=0?(v+5)/10:(v-5)/10;
 snprintf(n,sizeof(n),"%d",temperature);fill=temperature<0?0:temperature>100?100:(unsigned)temperature;}else strcpy(n,"--");
 text(p,3,57,"TEMP",1);solid_bar(p,38,55,82,10,fill,flags&DASH_TEMP);
 text(p,127,57,n,1);int x=127+(int)strlen(n)*6;outline(p,x,55,3,3);text(p,x+5,57,"C",1);
 panel_invert(p);
}
