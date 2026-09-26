# Zorro Steering Sensor (ZSS) support for op0.11.2-zss
#
# ZSS (smartZSS ZSS_V02.ino) sends SECONDARY_STEER_ANGLE (0x23) on bus 0 at ~100 Hz:
#   ZORRO_STEER       high-resolution angle, zero = wherever the wheel was at ZSS power-on
#   (data[4..6] carry an angle rate from the firmware; not defined in toyota_zss.dbc and not used)
#   CHECKSUM          Toyota checksum; bad frames are dropped by CANParser and never reach this file
#
# ZSS is only used while openpilot is engaged. Every check below falls back to the stock angle,
# so the worst case is "stock behaviour". Torque limits are enforced by panda safety, which never
# reads ZSS.
#
# Status (logged through carlog -> cloudlog on every change):
#   disengaged   openpilot not engaged, stock angle
#   stale        no valid ZSS frame for STALE_FRAMES (missing, unplugged, or failing checksum)
#   calibrating  learning the ZSS -> stock offset, stock angle
#   active       ZSS angle in use
#   mismatch     this frame failed the angle cross-check, stock angle
#   lockout      too many mismatches, stock angle until the next engagement

from opendbc.car.carlog import carlog

STALE_FRAMES = 50            # CarState updates (100 Hz) without a valid ZSS frame -> stale (0.5 s)

OFFSET_SAMPLES = 20          # steady samples averaged to learn the offset (0.2 s)
OFFSET_MAX_RATE = 5.0        # deg/s, only learn the offset while the wheel is nearly still

ANGLE_DIFF_THRESHOLD = 4.0   # deg, max |stock - ZSS| after the offset is applied

FAULT_LIMIT = 10             # leaky counter: +1 per failed frame, -1 per good frame; at the limit -> lockout

LOG_INTERVAL_FRAMES = 100    # log the same status at most once per second


class ZSS:
  def __init__(self):
    self._frames_since_update = STALE_FRAMES
    self._zss_angle = 0.
    self._cruise_active_prev = False
    self._frame = 0
    self._status = ""
    self._last_log_frame: dict[str, int] = {}
    self._reset_engagement()

  @property
  def status(self) -> str:
    return self._status

  def update(self, cp_zss, stock_angle_deg: float, stock_rate_deg: float, cruise_active: bool) -> float:
    self._frame += 1

    # 1. freshness: vl_all only holds frames received (and checksum-valid) in this update cycle
    if len(cp_zss.vl_all["SECONDARY_STEER_ANGLE"]["ZORRO_STEER"]):
      self._frames_since_update = 0
      self._zss_angle = cp_zss.vl["SECONDARY_STEER_ANGLE"]["ZORRO_STEER"]
    else:
      self._frames_since_update = min(self._frames_since_update + 1, STALE_FRAMES)

    # 2. not engaged: stock, everything is re-learned on the next engagement
    if not cruise_active:
      self._cruise_active_prev = False
      return self._fallback(stock_angle_deg, "disengaged")

    if not self._cruise_active_prev:
      self._reset_engagement()
    self._cruise_active_prev = True

    if self._frames_since_update >= STALE_FRAMES:
      return self._fallback(stock_angle_deg, "stale", f"no valid 0x23 for {STALE_FRAMES} frames")

    if self._locked_out:
      return self._fallback(stock_angle_deg, "lockout")

    # 3. offset: average over steady samples, not a single sample at the engage instant
    if self._offset is None:
      if abs(stock_rate_deg) < OFFSET_MAX_RATE:
        self._offset_samples.append(self._zss_angle - stock_angle_deg)
      else:
        self._offset_samples.clear()
      if len(self._offset_samples) < OFFSET_SAMPLES:
        return self._fallback(stock_angle_deg, "calibrating")
      self._offset = sum(self._offset_samples) / len(self._offset_samples)
      self._log("offset", f"offset learned: {self._offset:.3f} deg")

    zss_angle_deg = self._zss_angle - self._offset

    # 4. cross-check against the stock angle
    # (no angle-rate cross-check: the firmware rate field is not used until its frame period is verified)
    angle_diff = abs(stock_angle_deg - zss_angle_deg)
    if angle_diff > ANGLE_DIFF_THRESHOLD:
      self._fault_count += 1
      if self._fault_count >= FAULT_LIMIT:
        self._locked_out = True
        return self._fallback(stock_angle_deg, "lockout", f"angle diff {angle_diff:.2f} deg")
      return self._fallback(stock_angle_deg, "mismatch", f"angle diff {angle_diff:.2f} deg")

    self._fault_count = max(self._fault_count - 1, 0)
    self._set_status("active")
    return zss_angle_deg

  def _reset_engagement(self) -> None:
    self._offset: float | None = None
    self._offset_samples: list[float] = []
    self._fault_count = 0
    self._locked_out = False

  def _fallback(self, stock_angle_deg: float, status: str, detail: str = "") -> float:
    self._set_status(status, detail)
    return stock_angle_deg

  def _set_status(self, status: str, detail: str = "") -> None:
    if status != self._status:
      self._log(status, f"{self._status or 'init'} -> {status}" + (f" ({detail})" if detail else ""))
      self._status = status

  def _log(self, key: str, msg: str) -> None:
    last = self._last_log_frame.get(key)
    if last is None or self._frame - last >= LOG_INTERVAL_FRAMES:
      carlog.warning(f"ZSS: {msg}")
      self._last_log_frame[key] = self._frame
