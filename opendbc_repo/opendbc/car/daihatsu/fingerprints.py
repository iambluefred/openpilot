from opendbc.car.structs import CarParams
from opendbc.car.daihatsu.values import CAR

Ecu = CarParams.Ecu

# FPv1 (CAN) fingerprint, taken from a 153 s Gran Max highway capture.
#
# WARNING: FPv1 matching is superset-based -- a candidate is eliminated the
# moment the car sends any (address, length) pair that is not listed here. This
# capture is one highway drive, so messages that only appear at ignition-on, in
# P, with a door open, or with ACC engaged are almost certainly missing. Extend
# this from a fuller capture before relying on it.

FINGERPRINTS = {
  CAR.DAIHATSU_GRAN_MAX: [{
    160: 5, 161: 8, 164: 8, 165: 4, 308: 6, 398: 8, 399: 8, 400: 8, 409: 8, 410: 8, 416: 8, 417: 7, 427: 8, 429: 8,
    448: 4, 464: 8, 496: 5, 516: 8, 520: 6, 524: 6, 608: 8, 609: 8, 624: 8, 625: 8, 627: 8, 628: 8, 736: 8, 752: 8,
    848: 5, 856: 8, 857: 4, 900: 4, 912: 4, 976: 5, 980: 8, 1012: 7, 1032: 8, 1033: 8, 1034: 8, 1088: 8, 1090: 8,
    1100: 8, 1152: 8, 1160: 4, 1162: 8, 1163: 8, 1164: 8, 1168: 8, 1176: 3, 1188: 8, 1200: 3, 1217: 8, 1218: 8,
    1219: 8, 1224: 8, 1245: 8, 1247: 8, 1248: 8, 1267: 8, 1271: 8, 1312: 8, 1408: 8, 1409: 8, 1410: 8, 1416: 8,
    1417: 8, 1418: 8, 1434: 8, 1435: 8,
  }],
}

# TODO: no ECU firmware has been read off the car yet
FW_VERSIONS: dict[str, dict[tuple, list[bytes]]] = {
  CAR.DAIHATSU_GRAN_MAX: {},
}
