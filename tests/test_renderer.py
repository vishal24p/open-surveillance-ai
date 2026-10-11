import unittest
from unittest.mock import patch

import numpy as np

from surveillance.models import TrackedDetection
from surveillance.rendering.opencv import OpenCVRenderer, WINDOW_NAME, draw_person_detections


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


class OpenCVRendererTests(unittest.TestCase):
    def test_show_displays_frame_and_stops_only_on_q(self) -> None:
        frame = np.zeros((4, 4, 3), dtype=np.uint8)
        renderer = OpenCVRenderer()
        for key, keep_running in ((ord("q"), False), (-1, True), (ord("a"), True), (0x100 + ord("q"), False)):
            with self.subTest(key=key), patch("surveillance.rendering.opencv.cv2.imshow") as show, patch(
                "surveillance.rendering.opencv.cv2.waitKey", return_value=key
            ) as wait:
                self.assertEqual(renderer.show(frame), keep_running)
                self.assertEqual(show.call_args.args[0], WINDOW_NAME)
                self.assertIs(show.call_args.args[1], frame)
                wait.assert_called_once_with(1)

    def test_draw_uses_person_overlay_and_close_destroys_windows(self) -> None:
        frame = np.zeros((100, 200, 3), dtype=np.uint8)
        renderer = OpenCVRenderer()
        renderer.draw(frame, [])
        self.assertTrue(frame[:30, 75:].any())
        with patch("surveillance.rendering.opencv.cv2.destroyAllWindows") as destroy:
            renderer.close()
        destroy.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
