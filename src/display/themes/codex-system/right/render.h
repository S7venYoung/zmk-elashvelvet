/* SPDX-License-Identifier: MIT */
#pragma once
#include "../../../common/header.h"
static inline void system_render(uint8_t*p,const struct dashboard_status*s){
 memset(p,255,PANEL_BYTES);panel_header(p,s->keyboard);char n[24];const uint8_t flags=s->data[1];
 text(p,3,22,"CPU",1);solid_bar(p,38,20,82,10,s->data[3],flags&DASH_CPU);
 if(flags&DASH_CPU)snprintf(n,sizeof(n),"%u%%",s->data[3]);else strcpy(n,"--%");text(p,127,22,n,1);
 text(p,3,39,"RAM",1);solid_bar(p,38,37,82,10,s->data[4],flags&DASH_RAM);
 if(flags&DASH_RAM)snprintf(n,sizeof(n),"%u%%",s->data[4]);else strcpy(n,"--%");text(p,127,39,n,1);
 if(flags&DASH_RAM){unsigned used=(unsigned)dash_u16(s->data+10)*64,total=(unsigned)dash_u16(s->data+12)*64;
 unsigned tenth=(used*10+512)/1024;snprintf(n,sizeof(n),"%u.%u/%uG",tenth/10,tenth%10,total/1024);}else strcpy(n,"--/--G");
 /* Keep memory amount below its bar, not mixed into CPU temperature. */
 text(p,158-(int)strlen(n)*6,49,n,1);
 int temperature=0;unsigned fill=0;
 if(flags&DASH_TEMP){int v=(int16_t)dash_u16(s->data+8);temperature=v>=0?(v+5)/10:(v-5)/10;
 snprintf(n,sizeof(n),"%d",temperature);fill=temperature<0?0:temperature>100?100:(unsigned)temperature;}else strcpy(n,"--");
 text(p,3,59,"TEMP",1);solid_bar(p,38,57,82,10,fill,flags&DASH_TEMP);
 text(p,127,59,n,1);int x=127+(int)strlen(n)*6;outline(p,x,57,3,3);text(p,x+5,59,"C",1);
}
