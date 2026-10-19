/* SPDX-License-Identifier: MIT */
#pragma once
#include "pixels.h"
#include "dashboard_data.h"
static inline void panel_header(uint8_t*p,struct panel_status s){
 char n[8];outline(p,2,3,15,8);for(int i=0;i<4;i++)box(p,4+3*i,5,1,2,false);box(p,5,9,9,1,false);
 n[0]=s.side;n[1]=0;text(p,21,4,n,1);box(p,30,2,1,12,false);
 text(p,35,4,"BLE",1);for(int i=0;i<3;i++)box(p,55+3*i,10-i*2,2,1+i*2,s.connected?false:true);
 box(p,67,2,1,12,false);text(p,72,4,"USB",1);
 /* This is BLE split -> USB dongle, not a proprietary 2.4G radio. */
 outline(p,110,4,15,8);box(p,125,6,2,4,false);
 if(s.battery_valid)box(p,112,6,(int)s.battery*11/100,4,false);
 if(s.battery_valid)snprintf(n,sizeof(n),"%u%%",s.battery);else strcpy(n,"--%");
 text(p,130,4,n,1);box(p,1,16,158,1,false);
}
static inline void panel_layer(uint8_t*p,int x,int y,struct panel_status s){
 char n[6];outline(p,x,y,37,12);text(p,x+3,y+3,"LY",1);
 if(s.layer_valid)snprintf(n,sizeof(n),"%u",(unsigned)s.layer+1);else strcpy(n,"--");
 text(p,x+17,y+3,n,1);
}
