from dataclasses import dataclass

from ..models import TrackedDetection


DWELL_SECONDS = 2.0
POST_ROLL_SECONDS = 10.0


@dataclass(frozen=True, slots=True)
class ConfirmedIncident:
    started_at: float
    confirmed_at: float
    started_epoch: float
    confirmed_epoch: float


@dataclass(frozen=True, slots=True)
class CompletedIncident:
    incident: ConfirmedIncident
    exit_at: float
    exit_epoch: float
    closed_at: float
    closed_epoch: float
    duration_seconds: float


@dataclass(slots=True)
class _Scene:
    started_at: float
    started_epoch: float
    incident: ConfirmedIncident | None = None
    empty_at: float | None = None
    empty_epoch: float | None = None


class IncidentTracker:
    def __init__(self) -> None:
        self._scene: _Scene | None = None

    @property
    def pending_started_at(self) -> float | None:
        if self._scene is not None and self._scene.incident is None:
            return self._scene.started_at
        return None

    def update(
        self,
        detections: list[TrackedDetection],
        now: float,
        epoch: float,
    ) -> tuple[list[ConfirmedIncident], list[CompletedIncident]]:
        confirmed = []
        completed = []
        scene = self._scene
        if scene is not None and scene.empty_at is not None:
            if now >= scene.empty_at + POST_ROLL_SECONDS:
                completed.append(self._complete(scene))
                self._scene = scene = None

        if not detections:
            if scene is not None:
                if scene.incident is None:
                    self._scene = None
                elif scene.empty_at is None:
                    scene.empty_at = now
                    scene.empty_epoch = epoch
            return confirmed, completed

        if scene is None:
            scene = _Scene(now, epoch)
            self._scene = scene
        scene.empty_at = None
        scene.empty_epoch = None
        if scene.incident is None and now - scene.started_at >= DWELL_SECONDS:
            scene.incident = ConfirmedIncident(
                scene.started_at,
                now,
                scene.started_epoch,
                epoch,
            )
            confirmed.append(scene.incident)

        return confirmed, completed

    @staticmethod
    def _complete(scene: _Scene) -> CompletedIncident:
        assert scene.incident is not None
        assert scene.empty_at is not None
        assert scene.empty_epoch is not None
        return CompletedIncident(
            incident=scene.incident,
            exit_at=scene.empty_at,
            exit_epoch=scene.empty_epoch,
            closed_at=scene.empty_at + POST_ROLL_SECONDS,
            closed_epoch=scene.empty_epoch + POST_ROLL_SECONDS,
            duration_seconds=scene.empty_at - scene.incident.started_at,
        )
