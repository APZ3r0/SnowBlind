"""Pure decision logic. This module never controls physical actuators."""

from dataclasses import dataclass
from enum import Enum
import math
from typing import Iterable


class Action(str, Enum):
    STOP = "stop"
    FORWARD = "forward"


@dataclass(frozen=True)
class Decision:
    action: Action
    reason: str


class Controller:
    """Evaluate one complete scan at a time and latch on unsafe input."""

    def __init__(
        self,
        safety_distance_m: float = 0.3,
        obstacle_distance_mm: float = 1000.0,
    ) -> None:
        if not math.isfinite(safety_distance_m) or safety_distance_m <= 0:
            raise ValueError("safety_distance_m must be positive and finite")
        if not math.isfinite(obstacle_distance_mm) or obstacle_distance_mm <= 0:
            raise ValueError("obstacle_distance_mm must be positive and finite")
        self.safety_distance_m = safety_distance_m
        self.obstacle_distance_mm = obstacle_distance_mm
        self.latched = False

    def _stop(self, reason: str) -> Decision:
        self.latched = True
        return Decision(Action.STOP, reason)

    def evaluate(
        self,
        proximity_m: float | None,
        scan: Iterable[tuple[float, float, float]] | None,
    ) -> Decision:
        """Return a recommendation, never an actuator command.

        Scan entries use the RPLidar order (quality, angle degrees, distance mm).
        A valid return is required in each third of the forward 60-degree arc.
        """

        if self.latched:
            return Decision(Action.STOP, "latched_stop")

        try:
            proximity = float(proximity_m)
        except (TypeError, ValueError, OverflowError):
            return self._stop("invalid_proximity")
        if not math.isfinite(proximity) or proximity <= 0:
            return self._stop("invalid_proximity")
        if proximity <= self.safety_distance_m:
            return self._stop("proximity_breach")

        try:
            samples = iter(scan)
        except TypeError:
            return self._stop("invalid_scan")

        covered: set[int] = set()
        try:
            for sample in samples:
                _quality, raw_angle, raw_distance = sample
                angle = float(raw_angle)
                distance = float(raw_distance)
                if not math.isfinite(angle) or not math.isfinite(distance) or distance <= 0:
                    continue  # No valid return; this sector remains uncovered.
                relative_angle = (angle + 180.0) % 360.0 - 180.0
                if -30.0 <= relative_angle < -10.0:
                    sector = 0
                elif -10.0 <= relative_angle < 10.0:
                    sector = 1
                elif 10.0 <= relative_angle <= 30.0:
                    sector = 2
                else:
                    continue
                covered.add(sector)
                if distance < self.obstacle_distance_mm:
                    return self._stop("forward_obstacle")
        except (TypeError, ValueError, OverflowError):
            return self._stop("invalid_scan")

        if len(covered) != 3:
            return self._stop("incomplete_forward_scan")
        return Decision(Action.FORWARD, "clear")
