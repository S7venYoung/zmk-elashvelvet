/* SPDX-License-Identifier: MIT */
#pragma once
#include "../../../common/header.h"
static inline void codex_render(uint8_t*p,const struct dashboard_status*s){
 memset(p,255,PANEL_BYTES);panel_header(p,s->keyboard);
 tall_text(p,3,29,"CODEX");
 char n[20];bool q5=s->data[1]&DASH_QUOTA5,q7=s->data[1]&DASH_QUOTA7;
 if(q5)snprintf(n,sizeof(n),"5H %u%%",s->data[5]);else strcpy(n,"5H --%");
 text(p,68,23,n,1);bar(p,68,34,50,10,s->data[5],q5);
 if(q7)snprintf(n,sizeof(n),"7D %u%%",s->data[6]);else strcpy(n,"7D --%");
 text(p,68,49,n,1);bar(p,68,58,50,9,s->data[6],q7);
 box(p,121,21,1,46,false);text(p,125,23,"RESET",1);
 if(s->data[1]&DASH_RESET){uint32_t sec=dash_u32(s->data+14);unsigned h=(unsigned)(sec/3600);if(h>99)h=99;
 snprintf(n,sizeof(n),"%02u:%02u",h,(unsigned)(sec/60%60));}else strcpy(n,"--:--");
 text(p,125,36,n,1);panel_layer(p,123,54,s->keyboard);
}
