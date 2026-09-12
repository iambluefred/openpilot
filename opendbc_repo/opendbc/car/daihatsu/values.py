from dataclasses import dataclass, field

from opendbc.car import Bus, CarSpecs, DbcDict, PlatformConfig, Platforms
from opendbc.car.docs_definitions import CarDocs, CarHarness, CarParts
from opendbc.car.fw_query_definitions import FwQueryConfig, Request, StdQueries
from opendbc.car.structs import CarParams

Ecu = CarParams.Ecu

# Driver torque above which the wheel counts as held. Placeholder: it is not
# yet confirmed that STEERING_MODULE.MAIN_TORQUE is driver torque at all.
STEER_THRESHOLD = 20


class CarControllerParams:
  # TODO: no control message has been identified yet. Every value here is a
  #       placeholder and must not be trusted until the signal layer is done.
  STEER_MAX = 0
  STEER_STEP = 1

  def __init__(self, CP):
    pass


@dataclass
class DaihatsuCarDocs(CarDocs):
  package: str = "All"
  # TODO: harness is a guess. The CAN layer is Toyota-native, but the
  #       connector on the S403/S413 has not been checked.
  car_parts: CarParts = field(default_factory=CarParts.common([CarHarness.toyota_a]))


@dataclass(frozen=True, kw_only=True)
class DaihatsuCarSpecs(CarSpecs):
  tireStiffnessFactor: float = 0.7  # not measured


@dataclass
class DaihatsuPlatformConfig(PlatformConfig):
  dbc_dict: DbcDict = field(default_factory=lambda: {Bus.pt: 'daihatsu_granmax_generated'})


class CAR(Platforms):
  DAIHATSU_GRAN_MAX = DaihatsuPlatformConfig(
    [DaihatsuCarDocs("Daihatsu Gran Max 2025")],
    # Gran Max S403/S413. wheelbase is from the spec sheet; mass is the kerb
    # weight of the panel van. steerRatio is a placeholder, not measured.
    DaihatsuCarSpecs(mass=1300., wheelbase=2.65, steerRatio=17.5),
  )


FW_QUERY_CONFIG = FwQueryConfig(
  requests=[
    Request(
      [StdQueries.SHORT_TESTER_PRESENT_REQUEST, StdQueries.OBD_VERSION_REQUEST],
      [StdQueries.SHORT_TESTER_PRESENT_RESPONSE, StdQueries.OBD_VERSION_RESPONSE],
      bus=0,
    ),
  ],
)

DBC = CAR.create_dbc_map()
