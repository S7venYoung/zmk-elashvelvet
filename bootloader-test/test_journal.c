#define _GNU_SOURCE
#include <assert.h>
#include <setjmp.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
static bool cut;
static unsigned int erases;
static jmp_buf powered_off;
static void nrfx_nvmc_page_erase(uint32_t addr) {
  assert(addr==0x65000);erases++;memset((void *)(uintptr_t)addr,255,4096);
}
static void nrfx_nvmc_words_write(uint32_t addr,const uint32_t *src,uint32_t count) {
  assert(count==1 && addr>=0x65000 && addr<0x66000);
  uint32_t *dst=(uint32_t *)(uintptr_t)addr;
  assert((*dst & *src)==*src);*dst &= *src;
}
static void mock_delay(unsigned int ms) {
  assert(ms==2000);
  if(cut) longjmp(powered_off,1);
}
#define NRFX_DELAY_MS(ms) mock_delay(ms)
#include "nano_replug.h"
static void short_power(void) {
  cut=true;
  if(!setjmp(powered_off)){(void)nano_replug_boot(0);assert(0);}
  cut=false;
}
static uint8_t stage(void) {
  uint8_t value;uint32_t slot;
  assert(nano_journal_read(&value,&slot));return value;
}
int main(void) {
  void *p=mmap((void *)0x65000,4096,PROT_READ|PROT_WRITE,
               MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0);
  assert(p==(void *)0x65000);memset(p,255,4096);
  short_power();assert(stage()==1);
  short_power();assert(stage()==2);
  assert(nano_replug_boot(0));assert(stage()==0);
  assert(!nano_replug_boot(0));assert(stage()==0);
  for(unsigned int i=0;i<20;i++)assert(!nano_replug_boot(8));
  assert(stage()==0);
  memset(p,255,4096);
  for(int i=0;i<1024;i++)assert(nano_journal_append(0));
  unsigned int before=erases;
  assert(!nano_replug_boot(0));assert(erases==before+1 && stage()==0);
  memset(p,255,4096);*(uint32_t *)p=0x12345678;
  before=erases;assert(nano_replug_boot(0));assert(erases==before);
  assert(*(uint32_t *)p==0x12345678);
  puts("Journal tests passed: real policy/flash code, two power cuts, third-entry, normal clear, watchdog reset, full-page compaction, foreign-data preservation");
}
