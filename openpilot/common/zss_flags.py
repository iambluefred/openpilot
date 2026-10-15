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


def get_bool(name: str, default: bool = False) -> bool:
  try:
    with open(os.path.join(BASE_DIR, name)) as f:
      return f.read().strip() == "1"
  except (FileNotFoundError, OSError):
    return default


def put_bool(name: str, value: bool) -> None:
  os.makedirs(BASE_DIR, exist_ok=True)
  path = os.path.join(BASE_DIR, name)
  tmp = path + ".tmp"
  with open(tmp, "w") as f:
    f.write("1" if value else "0")
    f.flush()
    os.fsync(f.fileno())
  os.replace(tmp, path)  # atomic: a reader never sees a half-written file
