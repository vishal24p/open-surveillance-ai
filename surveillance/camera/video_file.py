from math import isfinite
from pathlib import Path

import cv2


class VideoFileSource:
    def __init__(self, path: Path) -> None:
        if not path.is_file():
            raise RuntimeError(f"Not a local video file: {path}")

        self._path = path
        self._capture = cv2.VideoCapture(str(path))
        if not self._capture.isOpened():
            self._capture.release()
            raise RuntimeError(f"Could not open video file: {path}")

        self.position_seconds: float | None = None

    def read(self):
        ok, frame = self._capture.read()
        if not ok:
            if self.position_seconds is None:
                raise RuntimeError(f"No frames could be decoded from video file: {self._path}")
            return False, None

        position = self._capture.get(cv2.CAP_PROP_POS_MSEC) / 1000
        if (
            not isfinite(position)
            or position < 0
            or (self.position_seconds is not None and position <= self.position_seconds)
        ):
            raise RuntimeError(
                f"Video timestamps must be finite, non-negative, and strictly increasing: {self._path}"
            )

        self.position_seconds = position
        return True, frame

    def close(self) -> None:
        self._capture.release()
