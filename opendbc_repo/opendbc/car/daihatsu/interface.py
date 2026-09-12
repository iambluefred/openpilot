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

    # Receive-only port: the signal layer is not decoded and no control
    # message has been identified. This must stay True until both are done.
    ret.dashcamOnly = True

    ret.steerActuatorDelay = 0.1
    ret.steerLimitTimer = 0.4
    ret.centerToFront = ret.wheelbase * 0.44

    return ret
