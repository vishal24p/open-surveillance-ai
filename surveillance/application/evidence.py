from collections import deque
from datetime import datetime, timezone
import json
from pathlib import Path

import cv2
import numpy as np

from .incidents import (
    CompletedIncident,
    ConfirmedIncident,
    DWELL_SECONDS,
)


PRE_ROLL_SECONDS = 10.0
HISTORY_SECONDS = PRE_ROLL_SECONDS + DWELL_SECONDS + 0.5
OUTPUT_FPS = 30.0


class EvidenceRecorder:
    def __init__(self, output_dir: Path = Path("incidents"), writer_factory=None) -> None:
        self._output_dir = output_dir
        self._writer_factory = writer_factory or cv2.VideoWriter
        self._history: deque[tuple[float, bytes]] = deque()
        self._writers = {}

    def buffer_frame(self, frame, now: float, pending_started_at: float | None = None) -> None:
        # shortcut: JPEG pre-roll trades fidelity for lower RAM use; use lossless segments for audit-grade evidence.
        ok, encoded = cv2.imencode(
            ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 95]
        )
        if not ok:
            raise RuntimeError("Could not encode frame for incident evidence.")

        self._history.append((now, encoded.tobytes()))
        cutoff = now - HISTORY_SECONDS
        if pending_started_at is not None:
            cutoff = min(cutoff, pending_started_at - PRE_ROLL_SECONDS)
        while self._history and self._history[0][0] < cutoff:
            self._history.popleft()

    def write_active_frame(
        self,
        frame,
        now: float,
        completed: list[CompletedIncident],
    ) -> None:
        closed_at = {
            incident.incident.track_id: incident.closed_at
            for incident in completed
        }
        for track_id, writer in self._writers.items():
            deadline = closed_at.get(track_id, now)
            self._write_frame(
                writer, frame if now <= deadline else writer["last_frame"], min(now, deadline)
            )

    def start_incident(self, incident: ConfirmedIncident) -> Path:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        number = 1
        while True:
            incident_dir = self._output_dir / str(number)
            try:
                incident_dir.mkdir()
                break
            except FileExistsError:
                number += 1
        stamp = datetime.fromtimestamp(
            incident.started_epoch, timezone.utc
        ).strftime("%Y%m%dT%H%M%S%fZ")
        video_path = incident_dir / "incident.mp4"
        buffered = [
            (timestamp, data)
            for timestamp, data in self._history
            if timestamp >= incident.started_at - PRE_ROLL_SECONDS
        ]
        if not buffered:
            raise RuntimeError("No buffered frames are available for incident evidence.")

        first_frame = self._decode_frame(buffered[0][1])
        height, width = first_frame.shape[:2]
        writer = self._writer_factory(
            str(video_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            OUTPUT_FPS,
            (width, height),
        )
        record = {
            "handle": writer,
            "incident": incident,
            "video_path": video_path,
            "first_at": buffered[0][0],
            "frames_written": 0,
            "last_frame": first_frame,
        }
        try:
            if not writer.isOpened():
                raise RuntimeError(f"Could not create incident video: {video_path}")
            self._write_frame(record, first_frame, buffered[0][0])
            for timestamp, data in buffered[1:]:
                self._write_frame(record, self._decode_frame(data), timestamp)
        except BaseException:
            writer.release()
            raise

        self._writers[incident.track_id] = record
        return video_path

    @staticmethod
    def _write_frame(record, frame, now: float) -> None:
        # Fixed-FPS MP4: hold the previous image through gaps and drop excess captures.
        target = int((now - record["first_at"]) * OUTPUT_FPS + 1e-7)
        while record["frames_written"] <= target:
            image = frame if record["frames_written"] == target else record["last_frame"]
            record["handle"].write(image)
            record["frames_written"] += 1
        record["last_frame"] = frame

    def finish_incident(self, completed: CompletedIncident) -> None:
        record = self._writers.pop(completed.incident.track_id, None)
        if record is None:
            return

        try:
            self._write_frame(record, record["last_frame"], completed.closed_at)
        finally:
            record["handle"].release()
        metadata = self._metadata(record, completed)
        self._write_metadata(record["video_path"], metadata)

    def close(self) -> None:
        records = list(self._writers.values())
        self._writers.clear()
        first_error = None
        for record in records:
            try:
                record["handle"].release()
            except Exception as error:
                if first_error is None:
                    first_error = error
            try:
                self._write_metadata(record["video_path"], self._metadata(record, None))
            except Exception as error:
                if first_error is None:
                    first_error = error
        if first_error is not None:
            raise first_error

    @staticmethod
    def _decode_frame(data: bytes):
        frame = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            raise RuntimeError("Could not decode frame for incident evidence.")
        return frame

    @staticmethod
    def _metadata(record, completed: CompletedIncident | None) -> dict:
        incident = record["incident"]
        metadata = {
            "zone": "full_frame",
            "track_id": incident.track_id,
            "entry_time": _iso_time(incident.started_epoch),
            "confirmation_time": _iso_time(incident.confirmed_epoch),
            "evidence_clip_path": str(record["video_path"]),
            "complete": completed is not None,
        }
        if completed is not None:
            metadata.update(
                {
                    "exit_time": _iso_time(completed.exit_epoch),
                    "track_removed_at": _iso_time(completed.removed_epoch),
                    "closed_at": _iso_time(completed.closed_epoch),
                    "duration_seconds": completed.duration_seconds,
                }
            )
        return metadata

    @staticmethod
    def _write_metadata(video_path: Path, metadata: dict) -> None:
        metadata_path = video_path.with_suffix(".json")
        metadata_path.write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8",
        )


def _iso_time(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat()
