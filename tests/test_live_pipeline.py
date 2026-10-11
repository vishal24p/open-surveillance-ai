import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

from surveillance.application.live_pipeline import LivePipeline
from surveillance.application.evidence import EvidenceRecorder
from surveillance.application.incidents import IncidentTracker
from surveillance.models import TrackedDetection


class LivePipelineTests(unittest.TestCase):
    def test_delayed_confirmation_through_post_roll_saves_raw_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source, tracker, renderer = Mock(), Mock(), Mock()
            writer = Mock()
            saved_frames = []
            writer.write.side_effect = lambda frame: saved_frames.append(float(frame.mean()))
            times = list(range(-10, 1)) + [3] + list(range(4, 35)) + [44]
            source.read.side_effect = [
                (True, np.full((4, 5, 3), timestamp + 10, dtype=np.uint8))
                for timestamp in times
            ] + [(False, None)]
            person = TrackedDetection(0, 0, 4, 5, 0.9, 7)
            tracker.track.side_effect = [[person] if timestamp in (0, 3) else [] for timestamp in times]
            renderer.draw.side_effect = lambda frame, detections: frame.fill(255)
            renderer.show.return_value = True
            recorder = EvidenceRecorder(Path(directory), lambda *args: writer)

            with patch("surveillance.application.live_pipeline.monotonic", side_effect=times), patch(
                "surveillance.application.live_pipeline.time", side_effect=[1000 + timestamp for timestamp in times]
            ):
                LivePipeline(source, tracker, renderer, IncidentTracker(), recorder).run()

            self.assertEqual(saved_frames[0], 0)
            self.assertEqual(saved_frames[-1], 54)
            self.assertNotIn(255, saved_frames)
            self.assertEqual(len(saved_frames), 1621)
            metadata = json.loads(next(Path(directory).rglob("*.json")).read_text(encoding="utf-8"))
            self.assertTrue(metadata["complete"])
            self.assertEqual(metadata["duration_seconds"], 3)
            writer.release.assert_called_once()
            source.close.assert_called_once()
            renderer.close.assert_called_once()

    def test_cleanup_attempts_every_resource_even_when_one_fails(self) -> None:
        for failure in ("source", "renderer", "evidence"):
            with self.subTest(failure=failure):
                source, tracker, renderer, incidents, evidence = [Mock() for _ in range(5)]
                source.read.return_value = (False, None)
                resources = {"source": source, "renderer": renderer, "evidence": evidence}
                resources[failure].close.side_effect = OSError(failure)

                with self.assertRaisesRegex(OSError, failure):
                    LivePipeline(source, tracker, renderer, incidents, evidence).run()

                for resource in resources.values():
                    resource.close.assert_called_once()

    def test_tracking_failure_still_closes_every_resource(self) -> None:
        source, tracker, renderer, incidents, evidence = [Mock() for _ in range(5)]
        source.read.return_value = (True, np.zeros((4, 5, 3), dtype=np.uint8))
        tracker.track.side_effect = RuntimeError("tracking failed")

        with self.assertRaisesRegex(RuntimeError, "tracking failed"):
            LivePipeline(source, tracker, renderer, incidents, evidence).run()

        for resource in (source, renderer, evidence):
            resource.close.assert_called_once()

    def test_pipeline_preserves_raw_frame_and_passes_pending_entry(self) -> None:
        source, tracker, renderer, incidents, evidence = [Mock() for _ in range(5)]
        frame = np.zeros((4, 5, 3), dtype=np.uint8)
        source.read.return_value = (True, frame)
        tracker.track.return_value = []
        incidents.update.return_value = ([], [])
        incidents.pending_started_at = 1.0
        renderer.draw.side_effect = lambda displayed, detections: displayed.fill(255)
        renderer.show.return_value = False

        with patch("surveillance.application.live_pipeline.monotonic", return_value=4.0):
            LivePipeline(source, tracker, renderer, incidents, evidence).run()

        args = evidence.buffer_frame.call_args.args
        self.assertEqual(len(args), 3)
        self.assertEqual(args[1:], (4.0, 1.0))
        self.assertFalse(args[0].any())
        self.assertTrue(frame.all())
        for resource in (source, renderer, evidence):
            resource.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
