/* SPDX-License-Identifier: MIT */
#pragma once
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define PANEL_W 160
#define PANEL_H 68
#define PANEL_BYTES (PANEL_W*PANEL_H/8)
/* Packed MSB-first, 1=black, matching the preserved cat renderer. */
static inline void px(uint8_t *p,int x,int y,bool black) {
 if(x<0||x>=PANEL_W||y<0||y>=PANEL_H)return;
 unsigned i=(unsigned)y*PANEL_W+(unsigned)x;
 if(black)p[i/8]|=128u>>(i%8);else p[i/8]&=(uint8_t)~(128u>>(i%8));
}
static inline void box(uint8_t*p,int x,int y,int w,int h,bool black){
 for(int yy=y;yy<y+h;yy++)for(int xx=x;xx<x+w;xx++)px(p,xx,yy,black);
}
static inline void outline(uint8_t*p,int x,int y,int w,int h){
 box(p,x,y,w,1,false);box(p,x,y+h-1,w,1,false);box(p,x,y,1,h,false);box(p,x+w-1,y,1,h,false);
}
/* Five columns, bit 0 is the top row. */
static inline uint64_t glyph(char c){
 static const uint8_t digits[10][5]={
 {0x3e,0x51,0x49,0x45,0x3e},{0,0x42,0x7f,0x40,0},{0x42,0x61,0x51,0x49,0x46},
 {0x21,0x41,0x45,0x4b,0x31},{0x18,0x14,0x12,0x7f,0x10},{0x27,0x45,0x45,0x45,0x39},
 {0x3c,0x4a,0x49,0x49,0x30},{1,0x71,9,5,3},{0x36,0x49,0x49,0x49,0x36},{6,0x49,0x49,0x29,0x1e}};
 static const uint8_t letters[26][5]={
 {0x7e,0x11,0x11,0x11,0x7e},{0x7f,0x49,0x49,0x49,0x36},{0x3e,0x41,0x41,0x41,0x22},
 {0x7f,0x41,0x41,0x22,0x1c},{0x7f,0x49,0x49,0x49,0x41},{0x7f,9,9,9,1},
 {0x3e,0x41,0x49,0x49,0x7a},{0x7f,8,8,8,0x7f},{0,0x41,0x7f,0x41,0},
 {0x20,0x40,0x41,0x3f,1},{0x7f,8,0x14,0x22,0x41},{0x7f,0x40,0x40,0x40,0x40},
 {0x7f,2,0xc,2,0x7f},{0x7f,4,8,0x10,0x7f},{0x3e,0x41,0x41,0x41,0x3e},
 {0x7f,9,9,9,6},{0x3e,0x41,0x51,0x21,0x5e},{0x7f,9,0x19,0x29,0x46},
 {0x46,0x49,0x49,0x49,0x31},{1,1,0x7f,1,1},{0x3f,0x40,0x40,0x40,0x3f},
 {0x1f,0x20,0x40,0x20,0x1f},{0x3f,0x40,0x38,0x40,0x3f},{0x63,0x14,8,0x14,0x63},
 {7,8,0x70,8,7},{0x61,0x51,0x49,0x45,0x43}};
 const uint8_t *a=NULL;uint8_t other[5]={0};
 if(c>='0'&&c<='9')a=digits[c-'0'];else if(c>='A'&&c<='Z')a=letters[c-'A'];
 else {switch(c){case '-':memset(other,8,5);break;case '%':other[0]=0x63;other[1]=0x13;other[2]=8;other[3]=0x64;other[4]=0x63;break;
 case ':':other[2]=0x24;break;case '.':other[2]=0x40;break;case '/':other[0]=0x20;other[1]=0x10;other[2]=8;other[3]=4;other[4]=2;break;
 case '~':other[0]=8;other[1]=4;other[2]=8;other[3]=0x10;other[4]=8;break;default:break;}a=other;}
 uint64_t v=0;for(int i=0;i<5;i++)v|=(uint64_t)a[i]<<(i*8);return v;
}
static inline void text(uint8_t*p,int x,int y,const char*s,int scale){
 for(;*s;s++,x+=6*scale){uint64_t g=glyph(*s);for(int col=0;col<5;col++)for(int row=0;row<7;row++)
 if(g&(UINT64_C(1)<<(col*8+row)))box(p,x+col*scale,y+row*scale,scale,scale,false);}
}
static inline void bar(uint8_t*p,int x,int y,int w,int h,unsigned percent,bool valid){
 outline(p,x,y,w,h);if(!valid){text(p,x+3,y+2,"--",1);return;}
 unsigned fill=(percent>100?100:percent)*(unsigned)(w-4)/100;
 for(unsigned i=0;i<fill;i++)if(i%4!=3)box(p,x+2+(int)i,y+2,1,h-4,false);
}
/* Narrow 3x5 footer lettering and tall display lettering. */
static inline uint16_t tiny_glyph(char c){
 switch(c){
 case 'L':return 0x4927;case 'A':return 0x2bed;case 'Y':return 0x5a92;case 'E':return 0x79a7;case 'R':return 0x6bad;
 case '0':return 0x7b6f;case '1':return 0x2c97;case '2':return 0x73e7;case '3':return 0x73cf;case '4':return 0x5bc9;
 case '5':return 0x79cf;case '6':return 0x79ef;case '7':return 0x7249;case '8':return 0x7bef;case '9':return 0x7bcf;
 case '-':return 0x01c0;default:return 0;}
}
static inline void tiny_text(uint8_t*p,int x,int y,const char*s){
 for(;*s;s++,x+=4){uint16_t g=tiny_glyph(*s);for(int row=0;row<5;row++)for(int col=0;col<3;col++)
 if(g&(1u<<(14-row*3-col)))px(p,x+col,y+row,false);}
}
static inline void tall_text(uint8_t*p,int x,int y,const char*s){
 for(;*s;s++,x+=12){uint64_t g=glyph(*s);for(int col=0;col<5;col++)for(int row=0;row<7;row++)
 if(g&(UINT64_C(1)<<(col*8+row)))box(p,x+col*2,y+row*3,2,3,false);}
}
