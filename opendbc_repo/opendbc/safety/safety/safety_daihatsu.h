#pragma once

#include "safety_declarations.h"

// Daihatsu Gran Max (S403/S413)
//
// Also sold as the Toyota Townace/Liteace and the Mazda Bongo. Despite the
// Mazda badge on some markets, the CAN layer is Daihatsu/Toyota native:
// the frame checksum is byte-for-byte identical to the Toyota scheme
// (verified 100% over 216327 frames across 47 IDs from a highway capture).
// It is NOT the Mazda scheme, which is subtractive and excludes the CAN ID
// and DLC. See opendbc/dbc/daihatsu_granmax_generated.dbc.
//
// STATUS: skeleton. The signal layer is not decoded yet, so this policy is
// receive-only -- every TX is rejected and nothing is blocked from the
// camera bus. Do not ship this as a controllable car.

// CAN msgs we care about
// TODO: assign real roles once the signal layer is decoded
#define DAIHATSU_MSG_0A4  0x0A4U  // 10.0 ms  (100 Hz), 8 bytes
#define DAIHATSU_MSG_0A1  0x0A1U  // 12.0 ms  ( 83 Hz), 8 bytes
#define DAIHATSU_MSG_134  0x134U  // 12.3 ms  ( 81 Hz), 6 bytes
#define DAIHATSU_MSG_190  0x190U  // 16.4 ms  ( 61 Hz), 8 bytes
#define DAIHATSU_MSG_1AB  0x1ABU  // 20.0 ms  ( 50 Hz), 8 bytes
#define DAIHATSU_MSG_1C0  0x1C0U  // 24.0 ms  ( 42 Hz), 4 bytes
// lowcostPedal board (Town Ace, Fred 2026-11-24, option B): its own cruise state, Toyota checksum.
// byte 1 = CRUISE_STATE: 0 OFF, 1 READY, 2 CRUISE, 3 OVERRIDE, 4 FAULT
#define DAIHATSU_SCM_BUTTONS  0x1A6U  // 20.0 ms  ( 50 Hz), 8 bytes

// CAN bus numbers
#define DAIHATSU_MAIN 0U
#define DAIHATSU_CAM  2U

// Frame checksum, identical to Toyota:
//   last_byte = (sum(data[:-1]) + (addr & 0xFF) + (addr >> 8) + len) & 0xFF
static uint32_t daihatsu_compute_checksum(const CANPacket_t *to_push) {
  int addr = GET_ADDR(to_push);
  int len = GET_LEN(to_push);
  uint8_t checksum = (uint8_t)(addr) + (uint8_t)((unsigned int)(addr) >> 8U) + (uint8_t)(len);
  for (int i = 0; i < (len - 1); i++) {
    checksum += (uint8_t)GET_BYTE(to_push, i);
  }
  return checksum;
}

static uint32_t daihatsu_get_checksum(const CANPacket_t *to_push) {
  int checksum_byte = GET_LEN(to_push) - 1U;
  return (uint8_t)(GET_BYTE(to_push, checksum_byte));
}

static void daihatsu_rx_hook(const CANPacket_t *to_push) {
  // Controls follow the lowcostPedal board's cruise (option B): allowed on the rising edge of
  // CRUISE / OVERRIDE, cleared as soon as the board leaves them (brake, cancel, fault, ...).
  // Only checksum-valid 0x1A6 frames get here (rx check below). If the board stops sending, the rx
  // check lags and safety_tick() clears controls_allowed.
  // TODO: vehicle_moving, gas_pressed, brake_pressed, torque_driver (no TX, so generic checks never run)
  if ((GET_BUS(to_push) == DAIHATSU_MAIN) && (GET_ADDR(to_push) == DAIHATSU_SCM_BUTTONS)) {
    uint8_t cruise_state = GET_BYTE(to_push, 1);
    pcm_cruise_check((cruise_state == 2U) || (cruise_state == 3U));
  }
}

// GCOV_EXCL_START
// Unreachable by design (no tx msgs are declared)
static bool daihatsu_tx_hook(const CANPacket_t *to_send) {
  UNUSED(to_send);
  return false;
}
// GCOV_EXCL_STOP

static bool daihatsu_fwd_hook(int bus, int addr) {
  UNUSED(bus);
  UNUSED(addr);
  // TODO: block the LKAS/HUD messages from DAIHATSU_CAM once they are found
  return false;
}

static safety_config daihatsu_init(uint16_t param) {
  static RxCheck daihatsu_rx_checks[] = {
    {.msg = {{DAIHATSU_MSG_0A4, DAIHATSU_MAIN, 8, .ignore_checksum = false, .ignore_counter = true, .frequency = 100U}, { 0 }, { 0 }}},
    {.msg = {{DAIHATSU_MSG_0A1, DAIHATSU_MAIN, 8, .ignore_checksum = false, .ignore_counter = true, .frequency =  83U}, { 0 }, { 0 }}},
    {.msg = {{DAIHATSU_MSG_134, DAIHATSU_MAIN, 6, .ignore_checksum = false, .ignore_counter = true, .frequency =  81U}, { 0 }, { 0 }}},
    {.msg = {{DAIHATSU_MSG_190, DAIHATSU_MAIN, 8, .ignore_checksum = false, .ignore_counter = true, .frequency =  61U}, { 0 }, { 0 }}},
    {.msg = {{DAIHATSU_MSG_1AB, DAIHATSU_MAIN, 8, .ignore_checksum = false, .ignore_counter = true, .frequency =  50U}, { 0 }, { 0 }}},
    {.msg = {{DAIHATSU_MSG_1C0, DAIHATSU_MAIN, 4, .ignore_checksum = false, .ignore_counter = true, .frequency =  42U}, { 0 }, { 0 }}},
    // lowcostPedal 0x1A6. Without the board this check lags: rx checks invalid, so openpilot shows
    // "Controls Mismatch" only as a no-entry when engaging, which cannot happen without the board anyway.
    {.msg = {{DAIHATSU_SCM_BUTTONS, DAIHATSU_MAIN, 8, .ignore_checksum = false, .ignore_counter = true, .frequency = 50U}, { 0 }, { 0 }}},
  };

  UNUSED(param);
  // receive-only: rx checks, but no tx msgs and the relay stays closed
  return (safety_config){daihatsu_rx_checks,
                         sizeof(daihatsu_rx_checks) / sizeof(daihatsu_rx_checks[0]),
                         NULL, 0, true};
}

const safety_hooks daihatsu_hooks = {
  .init = daihatsu_init,
  .rx = daihatsu_rx_hook,
  .tx = daihatsu_tx_hook,
  .fwd = daihatsu_fwd_hook,
  .get_checksum = daihatsu_get_checksum,
  .compute_checksum = daihatsu_compute_checksum,
};
