#!/usr/bin/env bash

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1

if [ -z "$AGNOS_VERSION" ]; then
  export AGNOS_VERSION="11.11"
fi

export STAGING_ROOT="/data/safe_staging"

# Town Ace (Fred 2026-11-24): do not send any diagnostic CAN (VIN / ECU / firmware queries) at startup.
# The car is recognised from the CAN fingerprint only (daihatsu has no FW_VERSIONS anyway).
# opendbc/car/car_helpers.py fingerprint(): SKIP_FW_QUERY skips get_vin, get_present_ecus, get_fw_versions.
export SKIP_FW_QUERY=1
# The relay stays in pass-through for the Town Ace, so the car is on panda bus 2, which the CAN fingerprint
# (buses 0 and 1) does not look at: fix the platform. This device is used on the Town Ace only.
export FINGERPRINT=DAIHATSU_GRAN_MAX
