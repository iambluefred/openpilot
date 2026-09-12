from opendbc.can.packer import CANPacker
from opendbc.car import Bus, structs
from opendbc.car.interfaces import CarControllerBase


class CarController(CarControllerBase):
  """Gran Max car controller.

  No control message has been identified on this car yet, and the safety
  policy (safety_daihatsu.h) rejects every TX. This sends nothing.
  """

  def __init__(self, dbc_names, CP):
    super().__init__(dbc_names, CP)
    self.packer = CANPacker(dbc_names[Bus.pt])

  def update(self, CC, CS, now_nanos):
    actuators = structs.CarControl.Actuators()
    # TODO: build the LKAS message here once it is found on the camera bus
    return actuators, []
