/* SPDX-License-Identifier: MIT */
#pragma once
#include "../../../common/header.h"
static inline void codex_render(uint8_t*p,const struct dashboard_status*s){
 memset(p,255,PANEL_BYTES);panel_header(p,s->keyboard);char n[20];
 const uint8_t flags=s->data[1];
 text(p,3,23,"5H",1);solid_bar(p,38,21,82,10,s->data[5],flags&DASH_QUOTA5);
 if(flags&DASH_QUOTA5)snprintf(n,sizeof(n),"%u%%",s->data[5]);else strcpy(n,"--%");text(p,127,23,n,1);
 text(p,3,40,"7D",1);solid_bar(p,38,38,82,10,s->data[6],flags&DASH_QUOTA7);
 if(flags&DASH_QUOTA7)snprintf(n,sizeof(n),"%u%%",s->data[6]);else strcpy(n,"--%");text(p,127,40,n,1);
 text(p,3,57,"RESET",1);
 uint32_t reset=dash_u32(s->data+14),minutes=reset&~DASH_RESET_CLOCK;
 if((flags&DASH_RESET)&&(reset&DASH_RESET_CLOCK)&&minutes<1440u)
  snprintf(n,sizeof(n),"%02u:%02u",(unsigned)(minutes/60),(unsigned)(minutes%60));
 else strcpy(n,"--:--");
 text(p,127,57,n,1);
}
