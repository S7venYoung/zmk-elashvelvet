#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include "replug_policy.h"
int main(void) {
  assert(!nano_record_valid(NANO_ERASED));
  assert(!nano_record_valid(0));
  assert(!nano_record_valid(NANO_RECORD_MAGIC | 3));
  for (uint8_t stage=0; stage<=2;stage++) {
    assert(nano_record_valid(NANO_RECORD_MAGIC | stage));
    assert(!nano_enter_dfu(stage,false));
  }
  uint8_t stage=0;
  stage=nano_next_stage(stage); assert(stage==1 && !nano_enter_dfu(stage,true));
  stage=nano_next_stage(stage); assert(stage==2 && nano_enter_dfu(stage,true));
  /* A normal boot clears the journal before jumping to the app. */
  stage=0;assert(!nano_enter_dfu(stage,true));
  assert(nano_next_stage(stage)==1);
  puts("Policy tests passed: short power sequence, normal boot clear, non-power resets, invalid records");
}
