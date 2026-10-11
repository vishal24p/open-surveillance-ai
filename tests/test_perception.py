import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np

from surveillance.perception.yolo_tracker import (
    MODEL_NAME,
    TRACKER_CONFIG,
    YoloTracker,
    extract_tracked_detections,
)


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


class YoloTrackerTests(unittest.TestCase):
    def test_missing_cuda_fails_before_model_load(self) -> None:
        torch = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False))
        load_model = Mock()
        with patch.dict("sys.modules", {"torch": torch, "ultralytics": SimpleNamespace(YOLO=load_model)}):
            with self.assertRaisesRegex(RuntimeError, "CUDA is required"):
                YoloTracker(0.8)
        load_model.assert_not_called()

    def test_track_preserves_ids_and_passes_person_gpu_tracking_settings(self) -> None:
        torch = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: True))
        model = Mock()
        model.track.return_value = [SimpleNamespace(boxes=FakeBoxes([(1, 2, 3, 4, 0.9)], [7]))]
        load_model = Mock(return_value=model)
        with patch.dict("sys.modules", {"torch": torch, "ultralytics": SimpleNamespace(YOLO=load_model)}):
            tracker = YoloTracker(0.8)
        frame = np.zeros((4, 4, 3), dtype=np.uint8)

        detections = tracker.track(frame)

        load_model.assert_called_once_with(MODEL_NAME)
        self.assertIs(model.track.call_args.args[0], frame)
        self.assertEqual(model.track.call_args.kwargs, {
            "persist": True, "classes": [0], "conf": 0.8, "device": 0,
            "tracker": str(TRACKER_CONFIG), "verbose": False,
        })
        self.assertEqual(detections[0].track_id, 7)


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
