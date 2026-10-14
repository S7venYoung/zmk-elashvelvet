/* Cube-only discovery identity; native ZMK split GATT/positions are unchanged.
 */
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/bluetooth/uuid.h>
#include <zephyr/init.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/byteorder.h>
#include <zmk/sensors.h>

#if defined(CONFIG_SHIELD_VELVET_LEFT)
#define CUBE_SIDE 0
#elif defined(CONFIG_SHIELD_VELVET_RIGHT)
#define CUBE_SIDE 1
#else
#error Cube peripheral needs a left or right shield
#endif
#define CUBE_SET                                                               \
  0x43, 0x56, 0x50, 0x31, 0x6f, 0x37, 0x4d, 0x91, 0xa6, 0x2e, 0x88, 0x05,      \
      0xd4, 0x73, 0x9b, 0xc0
static struct bt_uuid_128 service_uuid = BT_UUID_INIT_128(CUBE_SET);
static struct bt_uuid_128 identity_uuid =
    BT_UUID_INIT_128(0x43, 0x56, 0x50, 0x31, 0x6f, 0x37, 0x4d, 0x91, 0xa6, 0x2e,
                     0x88, 0x05, 0xd4, 0x73, 0x9b, 0xc1);
static const uint8_t identity[] = {1, CUBE_SIDE, CUBE_SET};
static const uint8_t discovery[] = {CUBE_SET, 1, CUBE_SIDE};
static struct bt_uuid_128 capabilities_uuid =
    BT_UUID_INIT_128(0x43, 0x56, 0x50, 0x31, 0x6f, 0x37, 0x4d, 0x91, 0xa6, 0x2e,
                     0x88, 0x05, 0xd4, 0x73, 0x9b, 0xc2);
BUILD_ASSERT(ZMK_KEYMAP_SENSORS_LEN <= 2,
             "Cube supports at most two rotary sensors per half");
static ssize_t read_capabilities(struct bt_conn *conn,
                                 const struct bt_gatt_attr *attr, void *buffer,
                                 uint16_t length, uint16_t offset) {
  uint8_t caps[6] = {1, ZMK_KEYMAP_SENSORS_LEN, 0, 0, 0, 0};
#if ZMK_KEYMAP_HAS_SENSORS
  for (unsigned i = 0; i < ZMK_KEYMAP_SENSORS_LEN; ++i) {
    const struct zmk_sensor_config *config = zmk_sensors_get_config_at_index(i);
    if (config)
      sys_put_le16(config->triggers_per_rotation, caps + 2 + i * 2);
  }
#endif
  return bt_gatt_attr_read(conn, attr, buffer, length, offset, caps,
                           sizeof(caps));
}
static ssize_t read_identity(struct bt_conn *conn,
                             const struct bt_gatt_attr *attr, void *buffer,
                             uint16_t length, uint16_t offset) {
  return bt_gatt_attr_read(conn, attr, buffer, length, offset, identity,
                           sizeof(identity));
}
BT_GATT_SERVICE_DEFINE(
    cube_identity_service, BT_GATT_PRIMARY_SERVICE(&service_uuid),
    BT_GATT_CHARACTERISTIC(&identity_uuid.uuid, BT_GATT_CHRC_READ,
                           BT_GATT_PERM_READ_ENCRYPT, read_identity, NULL,
                           NULL),
    BT_GATT_CHARACTERISTIC(&capabilities_uuid.uuid, BT_GATT_CHRC_READ,
                           BT_GATT_PERM_READ_ENCRYPT, read_capabilities, NULL,
                           NULL));
static const struct bt_data advertisement[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR),
    BT_DATA_BYTES(BT_DATA_UUID16_SOME, 0x0f, 0x18),
    BT_DATA(BT_DATA_SVC_DATA128, discovery, sizeof(discovery))};
static void refresh_discovery(struct k_work *work);
static K_WORK_DELAYABLE_DEFINE(discovery_work, refresh_discovery);
static void refresh_discovery(struct k_work *work) {
  ARG_UNUSED(work);
  /* Replace only advertising data; never restart/erase native directed bonds.
     Zephyr rejects updates while advertising is inactive/directed. */
  (void)bt_le_adv_update_data(advertisement, ARRAY_SIZE(advertisement), NULL,
                              0);
  k_work_reschedule(&discovery_work, K_SECONDS(2));
}
static int cube_identity_init(void) {
  k_work_schedule(&discovery_work, K_MSEC(200));
  return 0;
}
SYS_INIT(cube_identity_init, APPLICATION, 95);
