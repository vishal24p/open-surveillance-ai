import unittest
from unittest.mock import Mock, patch

import cv2
import numpy as np

from surveillance.camera.droidcam import DroidCamSource


class DroidCamSourceTests(unittest.TestCase):
    def test_reads_frames_and_disconnect_with_msmf_and_releases_capture(self) -> None:
        capture = Mock()
        capture.isOpened.return_value = True
        frame = np.zeros((4, 4, 3), dtype=np.uint8)
        capture.read.side_effect = [(True, frame), (False, None)]
        with patch("surveillance.camera.droidcam.cv2.VideoCapture", return_value=capture) as open_capture:
            source = DroidCamSource(2)
            try:
                ok, received = source.read()
                self.assertTrue(ok)
                self.assertIs(received, frame)
                self.assertEqual(source.read(), (False, None))
            finally:
                source.close()

        open_capture.assert_called_once_with(2, cv2.CAP_MSMF)
        capture.release.assert_called_once_with()

    def test_failed_open_releases_capture_and_reports_camera_index(self) -> None:
        capture = Mock()
        capture.isOpened.return_value = False
        with patch("surveillance.camera.droidcam.cv2.VideoCapture", return_value=capture):
            with self.assertRaisesRegex(RuntimeError, "camera index 2"):
                DroidCamSource(2)

        capture.release.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
