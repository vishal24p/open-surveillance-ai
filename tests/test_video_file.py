import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import cv2
import numpy as np

from surveillance.camera.video_file import VideoFileSource


class VideoFileSourceTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "clip.mp4"
        self.path.touch()
        self.capture = Mock()
        self.capture.isOpened.return_value = True
        self.capture.read.return_value = (True, np.zeros((4, 4, 3), dtype=np.uint8))
        self.capture.get.return_value = 0.0
        capture_patch = patch(
            "surveillance.camera.video_file.cv2.VideoCapture", return_value=self.capture
        )
        self.create_capture = capture_patch.start()
        self.addCleanup(capture_patch.stop)

    def test_missing_file_or_directory_is_rejected_before_open(self) -> None:
        for path in (self.path.with_name("missing.mp4"), self.path.parent):
            with self.subTest(path=path):
                with self.assertRaisesRegex(RuntimeError, "local video file"):
                    VideoFileSource(path)
        self.create_capture.assert_not_called()

    def test_failed_open_releases_capture_and_names_file(self) -> None:
        self.capture.isOpened.return_value = False

        with self.assertRaisesRegex(RuntimeError, "clip.mp4"):
            VideoFileSource(self.path)

        self.capture.release.assert_called_once_with()

    def test_reads_frame_timestamps_and_preserves_position_at_eof(self) -> None:
        first_frame = np.zeros((4, 4, 3), dtype=np.uint8)
        last_frame = np.ones((4, 4, 3), dtype=np.uint8)
        self.capture.read.side_effect = [(True, first_frame), (True, last_frame), (False, None)]
        self.capture.get.side_effect = [0.0, 125.0]
        source = VideoFileSource(self.path)
        self.addCleanup(source.close)

        self.create_capture.assert_called_once_with(str(self.path))
        ok, frame = source.read()
        self.assertTrue(ok)
        self.assertIs(frame, first_frame)
        self.assertEqual(source.position_seconds, 0.0)
        ok, frame = source.read()
        self.assertTrue(ok)
        self.assertIs(frame, last_frame)
        self.assertEqual(source.position_seconds, 0.125)
        self.assertEqual(source.read(), (False, None))
        self.assertEqual(source.position_seconds, 0.125)
        self.assertEqual(self.capture.get.call_count, 2)
        self.capture.get.assert_called_with(cv2.CAP_PROP_POS_MSEC)

    def test_invalid_first_timestamp_is_rejected(self) -> None:
        for timestamp in (-1.0, float("nan"), float("inf"), float("-inf")):
            with self.subTest(timestamp=timestamp):
                self.capture.get.return_value = timestamp
                source = VideoFileSource(self.path)
                self.addCleanup(source.close)
                with self.assertRaisesRegex(RuntimeError, "timestamp"):
                    source.read()

    def test_invalid_or_non_increasing_later_timestamp_is_rejected(self) -> None:
        for timestamp in (0.0, 50.0, 100.0, -1.0, float("nan"), float("inf")):
            with self.subTest(timestamp=timestamp):
                self.capture.get.side_effect = [100.0, timestamp]
                source = VideoFileSource(self.path)
                self.addCleanup(source.close)
                source.read()
                with self.assertRaisesRegex(RuntimeError, "timestamp"):
                    source.read()
                self.assertEqual(source.position_seconds, 0.1)

    def test_empty_video_is_rejected(self) -> None:
        self.capture.read.return_value = (False, None)
        source = VideoFileSource(self.path)
        self.addCleanup(source.close)

        with self.assertRaisesRegex(RuntimeError, "No frames.*clip.mp4"):
            source.read()

        self.capture.get.assert_not_called()

    def test_close_releases_capture(self) -> None:
        source = VideoFileSource(self.path)

        source.close()

        self.capture.release.assert_called_once_with()


class VideoFileDecodeTests(unittest.TestCase):
    def test_generated_mp4_decodes_all_frames_with_media_time(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tiny.mp4"
            writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (16, 16))
            try:
                self.assertTrue(writer.isOpened())
                for index in range(4):
                    writer.write(np.full((16, 16, 3), index * 40, dtype=np.uint8))
            finally:
                writer.release()

            source = VideoFileSource(path)
            try:
                for index in range(4):
                    ok, frame = source.read()
                    self.assertTrue(ok)
                    self.assertEqual(frame.shape, (16, 16, 3))
                    self.assertAlmostEqual(source.position_seconds, index / 10)
                self.assertEqual(source.read(), (False, None))
                self.assertAlmostEqual(source.position_seconds, 0.3)
            finally:
                source.close()


if __name__ == "__main__":
    unittest.main()
