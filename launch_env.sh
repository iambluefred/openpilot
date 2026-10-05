#!/usr/bin/env bash

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1

# models get lower priority than ui
# - ui is ~5ms
# - modeld is 20ms
# - DM is 10ms
# in order to run ui at 60fps (16.67ms), we need to allow
# it to preempt the model workloads. we have enough
# headroom for this until ui is moved to the CPU.
export QCOM_PRIORITY=12

if [ -z "$AGNOS_VERSION" ]; then
  export AGNOS_VERSION="19.7"
fi

export STAGING_ROOT="/data/safe_staging"

# Prius c (NHP10): force the car model for this branch (zoom0.11.2-priusc).
# The car has no fingerprint/FW entries, so auto-detect would fall back to MOCK.
# Note: a platform picked in Settings > Vehicle (CarPlatformBundle) still wins
# over FINGERPRINT; pick "Toyota Prius c 2012-21" there or leave it empty.
export FINGERPRINT="TOYOTA_PRIUS_C"
export SKIP_FW_QUERY=1
