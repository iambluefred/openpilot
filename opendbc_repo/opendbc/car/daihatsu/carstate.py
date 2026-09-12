from opendbc.can.can_define import CANDefine
from opendbc.can.parser import CANParser
from opendbc.car import Bus, structs
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.daihatsu.values import DBC, STEER_THRESHOLD
from opendbc.car.interfaces import CarStateBase


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

    # gear. VAL_: 0 "P", 2 "D", 4 "N", 8 "R". Only D was seen on the capture.
    gear = int(cp.vl["TRANSMISSION"]["GEAR"])
    ret.gearShifter = self.parse_gear_shifter(self.shifter_values.get(gear))

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
    # TODO: gas / gasPressed  -- GAS_PEDAL (0x18E) APPS_1 scaling is wrong here
    # TODO: cruiseState       -- ACC was not engaged during the capture
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
    ]
    return {
      Bus.pt: CANParser(DBC[CP.carFingerprint][Bus.pt], pt_messages, 0),
    }
