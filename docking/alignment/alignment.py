"""Horizontal alignment from explicitly synthetic local positions."""

from dataclasses import dataclass
from math import hypot, isfinite

from docking.states import DockingInput


@dataclass(frozen=True)
class LocalPosition:
    north_m: float
    east_m: float
    origin_id: str
    frame: str = "local_ned"


@dataclass(frozen=True)
class AlignmentResult:
    valid: bool
    timestamp_s: float | None = None
    north_error_m: float | None = None
    east_error_m: float | None = None
    horizontal_error_m: float | None = None
    reason: str = ""

    def to_docking_input(self) -> DockingInput:
        return DockingInput(
            alignment_valid=self.valid,
            alignment_timestamp_s=self.timestamp_s,
            north_error_m=self.north_error_m,
            east_error_m=self.east_error_m,
        )


def calculate_alignment(
    pad: LocalPosition | None,
    vehicle: LocalPosition | None,
    timestamp_s: float | None,
) -> AlignmentResult:
    """Return pad minus vehicle offsets; freshness is checked by the controller.

    Both positions must use meters, local NED, and the same named origin.
    Missing or invalid data returns an unavailable result with no numeric offsets.
    """
    if timestamp_s is None or not isfinite(timestamp_s) or timestamp_s < 0:
        return AlignmentResult(False, reason="Invalid alignment timestamp")
    if pad is None or vehicle is None:
        return AlignmentResult(False, timestamp_s, reason="Missing position")
    if pad.frame != "local_ned" or vehicle.frame != "local_ned":
        return AlignmentResult(False, timestamp_s, reason="Expected local NED frame")
    if not pad.origin_id or pad.origin_id != vehicle.origin_id:
        return AlignmentResult(False, timestamp_s, reason="Position origins differ")
    coordinates = (pad.north_m, pad.east_m, vehicle.north_m, vehicle.east_m)
    if not all(isfinite(value) for value in coordinates):
        return AlignmentResult(False, timestamp_s, reason="Nonfinite position")

    north = pad.north_m - vehicle.north_m
    east = pad.east_m - vehicle.east_m
    distance = hypot(north, east)
    if not all(isfinite(value) for value in (north, east, distance)):
        return AlignmentResult(False, timestamp_s, reason="Alignment overflow")
    return AlignmentResult(True, timestamp_s, north, east, distance,
                           "Synthetic position alignment")
