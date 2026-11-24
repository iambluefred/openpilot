from opendbc.can.can_define import CANDefine
from opendbc.can.parser import CANParser
from opendbc.car import Bus, structs
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.daihatsu.values import DBC, STEER_THRESHOLD
from opendbc.car.interfaces import CarStateBase

GearShifter = structs.CarState.GearShifter

# lowcostPedal 0x1A6 SCM_BUTTONS (optional: the car works without the board)
SCM_TIMEOUT_NS = 300_000_000   # no 0x1A6 for this long (vs. BRAKE 0x0A1, 83 Hz) = board absent
SCM_CRUISING = (2, 3)          # CRUISE_STATE: 0 OFF, 1 READY, 2 CRUISE, 3 OVERRIDE, 4 FAULT
GAS_PRESSED_PCT = 2.0          # APPS_1 above this = gas pressed (released 0, light ~2 %)
# Town Ace (Fred 2026-11-24): the harness relay stays in pass-through (intercepting it made the car log DTCs);
# then the car's CAN reaches the panda on bus 2 only (measured: bus 2 ~1440 frames/s, 0x0A1 present, bus 0 empty).
CAR_BUS = 2


class CarState(CarStateBase):
  """Gran Max car state.

  Signals are inherited from perodua_psd_pt.dbc (Perodua Ativa) and verified
  against a 153 s Gran Max highway capture. Anything not verified on that
  capture is left as a TODO below rather than guessed.
  """

  def __init__(self, CP):
    super().__init__(CP)
    can_define = CANDefine(DBC[CP.carFingerprint][Bus.pt])
    self.shifter_values = can_define.dv["TRANSMISSION"]["GEAR"]
    self.last_gear = GearShifter.unknown

  def update(self, can_parsers) -> structs.CarState:
    cp = can_parsers[Bus.pt]
    ret = structs.CarState()

    # speed. BRAKE.SPEED and BUTTONS.UI_SPEED carry the same raw value on this
    # car, which is how the 0.01 scaling was pinned down.
    speed_kph = cp.vl["BRAKE"]["SPEED"]
    ret.vEgoRaw = speed_kph * CV.KPH_TO_MS
    ret.vEgo, ret.aEgo = self.update_speed_kf(ret.vEgoRaw)
    ret.standstill = ret.vEgoRaw < 0.01

    # TODO: per-wheel speeds are not decoded yet. WHEEL_SPEED (0x1A0) carries
    #       Ativa scaling that does not hold on this car, and WHEEL_SPEED_CLEAN
    #       (0x260) decodes to nonsense here. Until then all four report the
    #       single vehicle speed.
    ret.wheelSpeeds = self.get_wheel_speeds(speed_kph, speed_kph, speed_kph, speed_kph)

    # steering
    ret.steeringAngleDeg = cp.vl["STEERING_MODULE"]["STEER_ANGLE"]
    # TODO: confirm whether MAIN_TORQUE is driver torque or EPS motor torque.
    #       On the highway capture it sits at 0 with a -60..+50 spread.
    ret.steeringTorque = cp.vl["STEERING_MODULE"]["MAIN_TORQUE"]
    ret.steeringPressed = self.update_steering_pressed(abs(ret.steeringTorque) > STEER_THRESHOLD, 5)

    # brakes
    ret.brakePressed = bool(cp.vl["BRAKE"]["BRAKE_ENGAGED"])
    ret.brake = cp.vl["BRAKE"]["BRAKE_PRESSURE"]
    ret.parkingBrake = bool(cp.vl["HANDBRAKE"]["HANDBRAKE_ENGAGED"])

    # gear (toyota_townace.dbc, verified on the Town Ace): P from PARK (byte 0 bit 0); GEAR is the whole
    # byte 1: 128 R, 64 N, 32 D, 16 "2", 8 L. GEAR is 0 in P and for ~0.1 s while the lever moves between
    # positions: keep the last gear then. "2" (2nd-gear hold) is reported as low, like L.
    gear = int(cp.vl["TRANSMISSION"]["GEAR"])
    if cp.vl["TRANSMISSION"]["PARK"]:
      self.last_gear = GearShifter.park
    elif gear != 0:
      name = self.shifter_values.get(gear)
      self.last_gear = GearShifter.low if name == "2" else self.parse_gear_shifter(name)
    ret.gearShifter = self.last_gear

    # gas: APPS_1 0-100 % (raw 0-6400, 1/64 %); engine rpm: APPS_3 raw = rpm (checked against the tachometer)
    apps_pct = cp.vl["GAS_PEDAL"]["APPS_1"]
    ret.gas = apps_pct / 100.
    ret.gasPressed = apps_pct > GAS_PRESSED_PCT
    ret.engineRpm = cp.vl["GAS_PEDAL"]["APPS_3"]

    # cruise: the lowcostPedal board runs its own cruise and reports it on 0x1A6 (optional message).
    # Option B (Fred 2026-11-24): openpilot engages (green border, engage sound) while the board cruises
    # (CRUISE_STATE CRUISE or OVERRIDE), panda safety follows the same signal (safety_daihatsu.h).
    # WARNING: this car has NO steering control yet (carcontroller sends nothing, panda rejects every TX):
    # engaged only means "the board's cruise is on"; openpilot does not steer.
    # available = board main switch on; speed = set speed only while the board is cruising.
    scm_ts = cp.ts_nanos["SCM_BUTTONS"]["CRUISE_STATE"]
    scm_fresh = scm_ts > 0 and (cp.ts_nanos["BRAKE"]["SPEED"] - scm_ts) < SCM_TIMEOUT_NS
    board_cruising = scm_fresh and int(cp.vl["SCM_BUTTONS"]["CRUISE_STATE"]) in SCM_CRUISING
    ret.cruiseState.available = scm_fresh and bool(cp.vl["SCM_BUTTONS"]["MAIN_ON"])
    ret.cruiseState.enabled = board_cruising
    set_ms = cp.vl["SCM_BUTTONS"]["SET_SPEED"] * CV.KPH_TO_MS if board_cruising else 0.
    ret.cruiseState.speed = set_ms
    ret.cruiseState.speedCluster = set_ms

    # blinkers, taken from the stalk. METER_CLUSTER (0x358) carries the lamp
    # state and agrees with the stalk on the capture, so it works as a check.
    ret.leftBlinker, ret.rightBlinker = self.update_blinker_from_stalk(
      50,
      bool(cp.vl["RIGHT_STALK"]["LEFT_SIGNAL"]),
      bool(cp.vl["RIGHT_STALK"]["RIGHT_SIGNAL"]),
    )

    # doors. All four read 0 for the whole capture, which matches a closed car,
    # but the polarity was never exercised.
    ret.doorOpen = any([cp.vl["METER_CLUSTER"]["MAIN_DOOR"],
                        cp.vl["METER_CLUSTER"]["LEFT_FRONT_DOOR"],
                        cp.vl["METER_CLUSTER"]["LEFT_BACK_DOOR"],
                        cp.vl["METER_CLUSTER"]["RIGHT_BACK_DOOR"]])

    # TODO: seatbeltUnlatched. METER_CLUSTER.SEAT_BELT_WARNING is stuck at 1 and
    #       SEAT_BELT_WARNING2 at 0 for the whole capture, with the driver belted.
    #       Polarity is unknown, so wiring it now would raise a permanent alert.
    # cruiseState.enabled: see above (option B: follows the board's cruise; no steering control)
    # TODO: steeringRateDeg   -- no rate signal identified
    # TODO: buttonEvents      -- PCM_BUTTONS (0x208) never changed on the capture

    ret.canValid = cp.can_valid
    return ret

  @staticmethod
  def get_can_parsers(CP):
    # frequencies measured off the capture
    pt_messages = [
      ("STEERING_MODULE", 100),
      ("BRAKE", 83),
      ("RIGHT_STALK", 33),
      ("TRANSMISSION", 31),
      ("METER_CLUSTER", 13),
      ("HANDBRAKE", 10),
      ("GAS_PEDAL", 60),
      ("SCM_BUTTONS", 0),   # lowcostPedal 50 Hz, optional: frequency 0 = no timeout check, see update()
    ]
    return {
      Bus.pt: CANParser(DBC[CP.carFingerprint][Bus.pt], pt_messages, CAR_BUS),
    }
