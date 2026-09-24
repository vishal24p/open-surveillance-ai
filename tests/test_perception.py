import unittest
from types import SimpleNamespace

import numpy as np

from surveillance.perception.yolo_tracker import extract_tracked_detections


class ExtractTrackedDetectionsTests(unittest.TestCase):
    def test_extracts_stable_ids_from_tracker_result(self) -> None:
        result = SimpleNamespace(
            boxes=FakeBoxes(
                [(20, 30, 80, 90, 0.91), (100, 30, 160, 90, 0.85)],
                [4, 9],
            )
        )

        detections = extract_tracked_detections(result)

        self.assertEqual(detections[0].track_id, 4)
        self.assertEqual(detections[1].track_id, 9)
        self.assertEqual(detections[0].x1, 20)

    def test_missing_tracker_ids_remain_none(self) -> None:
        result = SimpleNamespace(boxes=FakeBoxes([(20, 30, 80, 90, 0.91)]))

        detections = extract_tracked_detections(result)

        self.assertIsNone(detections[0].track_id)


class FakeBoxes:
    def __init__(self, detections, track_ids=None) -> None:
        self._boxes = [FakeBox(detection) for detection in detections]
        self.is_track = track_ids is not None
        self.id = None if track_ids is None else np.array(track_ids)

    def __iter__(self):
        return iter(self._boxes)


class FakeBox:
    def __init__(self, detection) -> None:
        x1, y1, x2, y2, confidence = detection
        self.xyxy = np.array([[x1, y1, x2, y2]], dtype=np.float64)
        self.conf = np.array([confidence], dtype=np.float64)


if __name__ == "__main__":
    unittest.main()
