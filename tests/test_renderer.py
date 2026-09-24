import unittest
from unittest.mock import patch

import numpy as np

from surveillance.models import TrackedDetection
from surveillance.rendering.opencv import draw_person_detections


class DrawPersonDetectionsTests(unittest.TestCase):
    def test_draws_each_person_box_and_top_right_count(self) -> None:
        frame = np.zeros((100, 200, 3), dtype=np.uint8)

        draw_person_detections(
            frame,
            [
                TrackedDetection(20, 30, 80, 90, 0.91, 4),
                TrackedDetection(100, 30, 160, 90, 0.85, 9),
            ],
        )

        self.assertTrue(frame[30, 20].any())
        self.assertTrue(frame[30, 100].any())
        self.assertTrue(frame[:30, 75:].any())

    def test_draws_zero_count_when_no_people_are_detected(self) -> None:
        frame = np.zeros((100, 200, 3), dtype=np.uint8)

        draw_person_detections(frame, [])

        self.assertTrue(frame[:30, 75:].any())

    def test_draws_track_id_when_tracker_provides_one(self) -> None:
        frame = np.zeros((100, 200, 3), dtype=np.uint8)

        with patch("surveillance.rendering.opencv.cv2.putText") as put_text:
            draw_person_detections(
                frame, [TrackedDetection(20, 30, 80, 90, 0.91, 4)]
            )

        labels = [call.args[1] for call in put_text.call_args_list]
        self.assertIn("person #4 91%", labels)

    def test_draws_person_without_fabricating_missing_track_id(self) -> None:
        frame = np.zeros((100, 200, 3), dtype=np.uint8)

        with patch("surveillance.rendering.opencv.cv2.putText") as put_text:
            draw_person_detections(
                frame, [TrackedDetection(20, 30, 80, 90, 0.91, None)]
            )

        labels = [call.args[1] for call in put_text.call_args_list]
        self.assertIn("person 91%", labels)


if __name__ == "__main__":
    unittest.main()
