from dataclasses import dataclass

from ..models import TrackedDetection


DWELL_SECONDS = 2.0
# Keep aligned with `track_buffer` in botsort_accuracy.yaml.
TRACK_LOST_FRAMES = 30
POST_ROLL_SECONDS = 10.0


@dataclass(frozen=True, slots=True)
class ConfirmedIncident:
    track_id: int
    started_at: float
    confirmed_at: float
    started_epoch: float
    confirmed_epoch: float


@dataclass(frozen=True, slots=True)
class CompletedIncident:
    incident: ConfirmedIncident
    exit_at: float
    exit_epoch: float
    removed_at: float
    removed_epoch: float
    closed_at: float
    closed_epoch: float
    duration_seconds: float


@dataclass(slots=True)
class _Track:
    started_at: float
    started_epoch: float
    last_seen_at: float
    last_seen_epoch: float
    missing_frames: int = 0
    incident: ConfirmedIncident | None = None
    removed_at: float | None = None
    removed_epoch: float | None = None


class IncidentTracker:
    def __init__(self) -> None:
        self._tracks: dict[int, _Track] = {}

    @property
    def pending_started_at(self) -> float | None:
        return min(
            (track.started_at for track in self._tracks.values() if track.incident is None),
            default=None,
        )

    def update(
        self,
        detections: list[TrackedDetection],
        now: float,
        epoch: float,
    ) -> tuple[list[ConfirmedIncident], list[CompletedIncident]]:
        confirmed = []
        completed = []
        seen_ids = {
            detection.track_id
            for detection in detections
            if detection.track_id is not None
        }

        for track_id in seen_ids:
            track = self._tracks.get(track_id)
            if track is None:
                track = _Track(now, epoch, now, epoch)
                self._tracks[track_id] = track
            elif track.removed_at is not None:
                if now > track.removed_at + POST_ROLL_SECONDS:
                    completed.append(self._complete(track))
                    track = _Track(now, epoch, now, epoch)
                    self._tracks[track_id] = track
                else:
                    track.removed_at = None
                    track.removed_epoch = None
                    track.missing_frames = 0

            track.last_seen_at = now
            track.last_seen_epoch = epoch
            track.missing_frames = 0
            if (
                track.incident is None
                and now - track.started_at >= DWELL_SECONDS
            ):
                track.incident = ConfirmedIncident(
                    track_id,
                    track.started_at,
                    now,
                    track.started_epoch,
                    epoch,
                )
                confirmed.append(track.incident)

        for track_id, track in list(self._tracks.items()):
            if track_id in seen_ids:
                continue

            track.missing_frames += 1
            if track.missing_frames <= TRACK_LOST_FRAMES:
                continue

            if track.incident is None:
                del self._tracks[track_id]
                continue

            if track.removed_at is None:
                track.removed_at = now
                track.removed_epoch = epoch
            elif now >= track.removed_at + POST_ROLL_SECONDS:
                completed.append(self._complete(track))
                del self._tracks[track_id]

        return confirmed, completed

    @staticmethod
    def _complete(track: _Track) -> CompletedIncident:
        assert track.incident is not None
        assert track.removed_at is not None
        assert track.removed_epoch is not None
        return CompletedIncident(
            incident=track.incident,
            exit_at=track.last_seen_at,
            exit_epoch=track.last_seen_epoch,
            removed_at=track.removed_at,
            removed_epoch=track.removed_epoch,
            closed_at=track.removed_at + POST_ROLL_SECONDS,
            closed_epoch=track.removed_epoch + POST_ROLL_SECONDS,
            duration_seconds=track.last_seen_at - track.incident.started_at,
        )
