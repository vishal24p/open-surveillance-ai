import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import main


class MainTests(unittest.TestCase):
    def test_video_flag_selects_file_and_media_clock_without_camera_settings(self) -> None:
        source = SimpleNamespace(position_seconds=2.5)
        with patch("sys.argv", ["main.py", "--video", "clip.mp4"]), patch.object(
            main, "VideoFileSource", return_value=source
        ) as video, patch.object(main, "DroidCamSource") as camera, patch.object(
            main, "get_person_confidence", return_value=0.8
        ), patch.object(main, "load_settings", side_effect=AssertionError("Loaded camera settings")), patch.object(
            main, "YoloTracker"
        ) as tracker, patch.object(main, "LivePipeline") as pipeline, patch.object(main, "time", return_value=1000):
            main.main()

        video.assert_called_once_with(Path("clip.mp4"))
        camera.assert_not_called()
        tracker.assert_called_once_with(0.8)
        self.assertIs(pipeline.call_args.args[0], source)
        clock = pipeline.call_args.kwargs["clock"]
        self.assertEqual(clock(), (2.5, 1002.5))
        source.position_seconds = 8
        self.assertEqual(clock(), (8, 1008))
        pipeline.return_value.run.assert_called_once()

    def test_no_flag_keeps_droidcam_and_default_pipeline_clock(self) -> None:
        with patch("sys.argv", ["main.py"]), patch.object(
            main, "load_settings", return_value=SimpleNamespace(droidcam_index=1, person_confidence=0.8)
        ), patch.object(main, "DroidCamSource") as camera, patch.object(
            main, "VideoFileSource"
        ) as video, patch.object(main, "YoloTracker"), patch.object(main, "LivePipeline") as pipeline:
            main.main()

        camera.assert_called_once_with(1)
        video.assert_not_called()
        self.assertIsNone(pipeline.call_args.kwargs["clock"])
        pipeline.return_value.run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
