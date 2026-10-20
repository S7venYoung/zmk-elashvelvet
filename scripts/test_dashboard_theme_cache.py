#!/usr/bin/env python3
"""Exercise the production settings callbacks without a Zephyr/flash device."""
from pathlib import Path
import subprocess
import tempfile
root=Path(__file__).resolve().parents[1]
s=(root/'src/display/dashboard_screen.c').read_text()
callbacks=s[s.index('static uint8_t saved_theme='):s.index('static int on_event(')]
program=r'''
#include <assert.h>
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <string.h>
#include <errno.h>
#define ARG_UNUSED(x) (void)(x)
#define CONFIG_ZMK_SETTINGS_SAVE_DEBOUNCE 100
#define K_MSEC(x) (x)
struct k_work {int unused;};
#define K_WORK_DELAYABLE_DEFINE(name,fn) static struct k_work name
#define SETTINGS_STATIC_HANDLER_DEFINE(...)
struct k_spinlock {int unused;};
typedef int k_spinlock_key_t;
static struct k_spinlock lock;
static int k_spin_lock(struct k_spinlock *p){(void)p;return 0;}
static void k_spin_unlock(struct k_spinlock *p,int k){(void)p;(void)k;}
static uint8_t theme;
static bool theme_known,received;
static int writes,reschedules,write_error;
static uint8_t disk;
static bool flip_during_write;
typedef int (*settings_read_cb)(void *,void *,size_t);
static bool settings_name_steq(const char *s,const char *key,const char **next){*next=NULL;return strcmp(s,key)==0;}
static int settings_save_one(const char *name,const void *p,size_t n){
 assert(strcmp(name,"velvet_panel/theme")==0&&n==1);writes++;
 if(flip_during_write){theme=0;flip_during_write=false;}
 if(write_error)return write_error;
 disk=*(const uint8_t *)p;return 0;
}
static void k_work_reschedule(struct k_work *w,int d){(void)w;(void)d;reschedules++;}
static int read_value(void *arg,void *out,size_t n){memcpy(out,arg,n);return (int)n;}
''' + callbacks + r'''
int main(void){
 assert(!theme_known); /* No default cat before a theme is known. */
 uint8_t value=1;
 assert(load_theme("theme",1,read_value,&value)==0);
 assert(theme_known&&theme==1); /* First frame restores the info suite. */
 save_theme(NULL);assert(writes==0);
 value=2;assert(load_theme("theme",1,read_value,&value)==-EINVAL);
 assert(theme==1);
 assert(load_theme("theme",2,read_value,&value)==-EINVAL);
 theme=0;save_theme(NULL);assert(writes==1&&disk==0);
 for(int i=0;i<100;i++)save_theme(NULL);
 assert(writes==1); /* Repeated telemetry cannot write flash. */
 theme=1;write_error=-EIO;save_theme(NULL);assert(saved_theme==0);
 write_error=0;save_theme(NULL);assert(disk==1&&saved_theme==1);
 theme=0;save_theme(NULL);
 theme=1;flip_during_write=true;save_theme(NULL);
 assert(reschedules==1&&theme==0&&saved_theme==1);
 save_theme(NULL);assert(disk==0&&saved_theme==0);
 received=true;theme=1;value=0;
 assert(load_theme("theme",1,read_value,&value)==0&&theme==1);
 return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text(program)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
print('Theme cache: startup, validation, write deduplication, retry and concurrent update passed')
