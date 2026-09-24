from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TrackedDetection:
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    track_id: int | None
