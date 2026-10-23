# op0.11.2-zss: small on/off settings stored as plain files.
#
# This branch ships prebuilt: the Params key list is compiled into libparams_c.so,
# so a new Params key would need a rebuild on the device. These settings are
# plain files instead: /data/personal_settings/<name> containing "1" or "0".
# A missing file means the setting's default (see each name below).

import os

BASE_DIR = "/data/personal_settings" if os.path.isdir("/data") else os.path.expanduser("~/.comma/personal_settings")

LANE_CHANGE_ENABLED = "LaneChangeEnabled"  # blinker lane change, default OFF
AEM_ENABLED = "AEMEnabled"                 # Adaptive Experimental Mode, default ON (get_bool(..., default=True))
EGPU_POWER_LIMIT = "EgpuPowerLimitW"       # DIY eGPU power limit in W, "0" = no limit, default "60" (read by modeld)
CAR_MODEL = "CarModel"                     # op0.11.2-priusc: "AUTO" (default) or a forced platform, read by card

CAR_MODEL_AUTO = "AUTO"
CAR_MODELS = (CAR_MODEL_AUTO, "TOYOTA_PRIUS_C")  # values the UI can store; anything else is treated as AUTO


def get_car_model() -> str:
  model = get_str(CAR_MODEL, CAR_MODEL_AUTO)
  return model if model in CAR_MODELS else CAR_MODEL_AUTO


def get_bool(name: str, default: bool = False) -> bool:
  try:
    with open(os.path.join(BASE_DIR, name)) as f:
      return f.read().strip() == "1"
  except (FileNotFoundError, OSError):
    return default


def get_str(name: str, default: str = "") -> str:
  try:
    with open(os.path.join(BASE_DIR, name)) as f:
      return f.read().strip() or default
  except (FileNotFoundError, OSError):
    return default


def put_bool(name: str, value: bool) -> None:
  put_str(name, "1" if value else "0")


def put_str(name: str, value: str) -> None:
  os.makedirs(BASE_DIR, exist_ok=True)
  path = os.path.join(BASE_DIR, name)
  tmp = path + ".tmp"
  with open(tmp, "w") as f:
    f.write(value)
    f.flush()
    os.fsync(f.fileno())
  os.replace(tmp, path)  # atomic: a reader never sees a half-written file
