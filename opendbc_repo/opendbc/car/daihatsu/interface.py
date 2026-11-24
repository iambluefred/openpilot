#!/usr/bin/env python3
from opendbc.car import get_safety_config, structs
from opendbc.car.daihatsu.carcontroller import CarController
from opendbc.car.daihatsu.carstate import CarState
from opendbc.car.interfaces import CarInterfaceBase


class CarInterface(CarInterfaceBase):
  CarState = CarState
  CarController = CarController

  @staticmethod
  def _get_params(ret: structs.CarParams, candidate, fingerprint, car_fw, experimental_long, docs) -> structs.CarParams:
    ret.brand = "daihatsu"
    ret.safetyConfigs = [get_safety_config(structs.CarParams.SafetyModel.daihatsu)]
    ret.radarUnavailable = True

    # Control output is still gated, but no longer by dashcamOnly: carcontroller
    # sends nothing, safety_daihatsu.h rejects every TX, and cruiseState is not
    # decoded, so pcmCruise can never enable openpilot. Turning this off lets
    # pandad actually apply SAFETY_DAIHATSU so the safety mode can be exercised.
    #
    # Fred 2026-11-24 (option B): cruiseState IS decoded from the lowcostPedal board's
    # 0x1A6, so openpilot engages while the board cruises. carcontroller still sends
    # no LKAS message: engaged = the board's longitudinal cruise only, NO steering.
    ret.dashcamOnly = False

    ret.steerActuatorDelay = 0.1
    ret.steerLimitTimer = 0.4
    ret.centerToFront = ret.wheelbase * 0.44

    return ret
