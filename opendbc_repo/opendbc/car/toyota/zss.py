# Zorro Steering Sensor (ZSS) support for op0.11.2-zss
#
# ZSS sends a high-resolution steering angle on bus 0 as SECONDARY_STEER_ANGLE (0x23).
# The absolute zero of ZSS is arbitrary, so an offset against the stock angle is learned
# every time openpilot engages. ZSS is only used while engaged; any doubt falls back to stock.

ANGLE_DIFF_THRESHOLD = 4.0  # deg, max allowed |stock - ZSS| after offset is applied
THRESHOLD_COUNT = 10        # mismatches allowed before ZSS is disabled until the next engagement
STALE_FRAMES = 50           # CarState updates (100 Hz) without a new ZSS message -> stale (0.5 s)


class ZSS:
  def __init__(self):
    self._offset_compute_required = True
    self._cruise_active_prev = False
    self._angle_offset = 0.
    self._threshold_count = 0
    self._frames_since_update = STALE_FRAMES
    self._zss_value = 0.

  def update(self, cp_zss, stock_steering_angle_deg: float, cruise_active: bool) -> float:
    # track freshness: vl_all only holds values received in this update cycle
    if len(cp_zss.vl_all["SECONDARY_STEER_ANGLE"]["ZORRO_STEER"]):
      self._frames_since_update = 0
      self._zss_value = cp_zss.vl["SECONDARY_STEER_ANGLE"]["ZORRO_STEER"]
    else:
      self._frames_since_update = min(self._frames_since_update + 1, STALE_FRAMES)

    # not engaged: use stock, re-learn offset on next engagement
    if not cruise_active:
      self._cruise_active_prev = False
      return stock_steering_angle_deg

    # rising edge of engagement: reset offset and error counter
    if not self._cruise_active_prev:
      self._offset_compute_required = True
      self._threshold_count = 0
    self._cruise_active_prev = True

    if self._frames_since_update >= STALE_FRAMES:
      return stock_steering_angle_deg

    if self._offset_compute_required:
      self._compute_offset(stock_steering_angle_deg)
      if self._offset_compute_required:
        return stock_steering_angle_deg

    # too many mismatches during this engagement: stay on stock
    if self._threshold_count >= THRESHOLD_COUNT:
      return stock_steering_angle_deg

    zss_steering_angle_deg = self._zss_value - self._angle_offset
    if abs(stock_steering_angle_deg - zss_steering_angle_deg) > ANGLE_DIFF_THRESHOLD:
      self._threshold_count += 1
      return stock_steering_angle_deg

    return zss_steering_angle_deg

  def _compute_offset(self, stock_steering_angle_deg: float) -> None:
    if abs(stock_steering_angle_deg) > 1e-3 and abs(self._zss_value) > 1e-3:
      self._angle_offset = self._zss_value - stock_steering_angle_deg
      self._offset_compute_required = False
