/* SPDX-License-Identifier: MIT */
#pragma once
#include "../../common/header.h"
static inline void codex_render(uint8_t*p,const struct dashboard_status*s){
 memset(p,255,PANEL_BYTES);panel_header(p,s->keyboard);
 text(p,3,24,"CODEX",2);text(p,3,43,"REMAIN",1);
 char n[20];bool q5=s->data[1]&DASH_QUOTA5,q7=s->data[1]&DASH_QUOTA7;
 if(q5)snprintf(n,sizeof(n),"5H %u%%",s->data[5]);else strcpy(n,"5H --%");text(p,69,22,n,1);bar(p,69,32,49,10,s->data[5],q5);
 if(q7)snprintf(n,sizeof(n),"7D %u%%",s->data[6]);else strcpy(n,"7D --%");text(p,69,46,n,1);bar(p,69,56,49,10,s->data[6],q7);
 box(p,120,21,1,45,false);text(p,125,22,"RESET",1);
 if(s->data[1]&DASH_RESET){uint32_t sec=dash_u32(s->data+14);unsigned h=(unsigned)(sec/3600);if(h>99)h=99;
 snprintf(n,sizeof(n),"%02u:%02u",h,(unsigned)(sec/60%60));}else strcpy(n,"--:--");
 text(p,125,34,n,1);panel_layer(p,122,52,s->keyboard);
}
