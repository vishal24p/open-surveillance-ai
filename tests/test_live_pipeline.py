import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import cv2

from surveillance.application.live_pipeline import LivePipeline
from surveillance.application.evidence import EvidenceRecorder
from surveillance.application.incidents import IncidentTracker
from surveillance.camera.video_file import VideoFileSource
from surveillance.models import TrackedDetection


class LivePipelineTests(unittest.TestCase):
    def test_short_visit_replay_creates_no_evidence_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source, tracker, renderer = Mock(), Mock(), Mock()
            frame = np.zeros((16, 16, 3), dtype=np.uint8)
            source.read.side_effect = [(True, frame)] * 3 + [(False, None)]
            tracker.track.side_effect = [[TrackedDetection(0, 0, 4, 5, 0.9, None)], [], []]
            renderer.show.return_value = True
            recorder = EvidenceRecorder(Path(directory) / "incidents")
            clock = iter(((0, 1000), (1, 1001), (20, 1020)))
            LivePipeline(source, tracker, renderer, IncidentTracker(), recorder, clock=clock.__next__).run()
            self.assertFalse((Path(directory) / "incidents").exists())
            source.close.assert_called_once()
            renderer.close.assert_called_once()

    def test_immediate_eof_does_not_process_frame_or_clock(self) -> None:
        source, tracker, renderer, incidents, evidence = [Mock() for _ in range(5)]
        source.read.return_value = (False, None)
        clock = Mock()
        LivePipeline(source, tracker, renderer, incidents, evidence, clock=clock).run()
        clock.assert_not_called()
        tracker.track.assert_not_called()
        incidents.update.assert_not_called()
        evidence.buffer_frame.assert_not_called()
        renderer.show.assert_not_called()
        for resource in (source, renderer, evidence):
            resource.close.assert_called_once()

    def test_q_stops_before_reading_another_frame(self) -> None:
        source, tracker, renderer, incidents, evidence = [Mock() for _ in range(5)]
        source.read.return_value = (True, np.zeros((4, 5, 3), dtype=np.uint8))
        tracker.track.return_value = []
        incidents.update.return_value = ([], [])
        incidents.pending_started_at = None
        renderer.show.return_value = False
        LivePipeline(source, tracker, renderer, incidents, evidence, clock=lambda: (0, 1000)).run()
        source.read.assert_called_once()
        evidence.buffer_frame.assert_called_once()
        for resource in (source, renderer, evidence):
            resource.close.assert_called_once()

    def test_incident_and_evidence_failures_close_all_resources(self) -> None:
        for failure in ("update", "buffer_frame", "write_active_frame", "start_incident", "finish_incident"):
            with self.subTest(failure=failure):
                source, tracker, renderer, incidents, evidence = [Mock() for _ in range(5)]
                source.read.return_value = (True, np.zeros((4, 5, 3), dtype=np.uint8))
                tracker.track.return_value = []
                confirmed = [Mock(started_at=0)] if failure == "start_incident" else []
                completed = [Mock()] if failure == "finish_incident" else []
                incidents.update.return_value = (confirmed, completed)
                incidents.pending_started_at = None
                target = incidents if failure == "update" else evidence
                getattr(target, failure).side_effect = RuntimeError(failure)
                with self.assertRaisesRegex(RuntimeError, failure):
                    LivePipeline(source, tracker, renderer, incidents, evidence, clock=lambda: (2, 1002)).run()
                for resource in (source, renderer, evidence):
                    resource.close.assert_called_once()

    def test_completion_finishes_before_next_confirmation_starts(self) -> None:
        source, tracker, renderer, evidence = [Mock() for _ in range(4)]
        source.read.side_effect = [(True, np.zeros((4, 5, 3), dtype=np.uint8))] * 6 + [(False, None)]
        person = TrackedDetection(0, 0, 4, 5, 0.9, None)
        tracker.track.side_effect = [[person], [person], [], [person], [person], []]
        renderer.show.return_value = True
        clock = iter((now, 1000 + now) for now in (0, 2, 3, 13, 15, 16))
        LivePipeline(source, tracker, renderer, IncidentTracker(), evidence, clock=clock.__next__).run()
        operations = [call[0] for call in evidence.mock_calls if call[0] in ("start_incident", "finish_incident")]
        self.assertEqual(operations, ["start_incident", "finish_incident", "start_incident"])
        self.assertEqual(evidence.start_incident.call_args_list[1].args[0].started_at, 13)

    def test_thirty_second_scene_with_individual_arrivals_has_one_incomplete_clip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source, tracker, renderer = Mock(), Mock(), Mock()
            source.read.side_effect = [
                (True, np.zeros((16, 16, 3), dtype=np.uint8)) for _ in range(31)
            ] + [(False, None)]
            people = [TrackedDetection(0, 0, 4, 5, 0.9, track_id) for track_id in (7, 8, 9)]
            tracker.track.side_effect = [
                people if 5 <= second < 10 or 15 <= second < 20 else people[:2]
                for second in range(31)
            ]
            renderer.show.return_value = True
            recorder = EvidenceRecorder(Path(directory))
            clock = iter((second, 1000 + second) for second in range(31))

            LivePipeline(source, tracker, renderer, IncidentTracker(), recorder, clock=clock.__next__).run()

            root = Path(directory)
            self.assertEqual([folder.name for folder in root.iterdir()], ["1"])
            self.assertEqual(sorted(file.name for file in (root / "1").iterdir()), ["incident.json", "incident.mp4"])
            metadata = json.loads((root / "1" / "incident.json").read_text(encoding="utf-8"))
            self.assertFalse(metadata["complete"])
            self.assertEqual(metadata["zone"], "full_frame")
            self.assertNotIn("track_id", metadata)
            capture = cv2.VideoCapture(str(root / "1" / "incident.mp4"))
            try:
                self.assertTrue(capture.isOpened())
                self.assertEqual(capture.get(cv2.CAP_PROP_FRAME_COUNT), 901)
            finally:
                capture.release()
            source.close.assert_called_once()
            renderer.close.assert_called_once()

    def test_sequential_frame_incidents_finish_separate_clips(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source, tracker, renderer = Mock(), Mock(), Mock()
            times = (0, 1, 2, 3, 13, 14, 15, 16, 26)
            source.read.side_effect = [
                (True, np.zeros((16, 16, 3), dtype=np.uint8)) for _ in times
            ] + [(False, None)]
            person = TrackedDetection(0, 0, 4, 5, 0.9, None)
            tracker.track.side_effect = [[person] if second in (0, 1, 2, 13, 14, 15) else [] for second in times]
            renderer.show.return_value = True
            clock = iter((second, 1000 + second) for second in times)
            recorder = EvidenceRecorder(Path(directory))

            with patch("builtins.print") as message:
                LivePipeline(source, tracker, renderer, IncidentTracker(), recorder, clock=clock.__next__).run()

            root = Path(directory)
            self.assertEqual(sorted(folder.name for folder in root.iterdir()), ["1", "2"])
            for number, exit_time, closed_at in (
                (1, "1970-01-01T00:16:43+00:00", "1970-01-01T00:16:53+00:00"),
                (2, "1970-01-01T00:16:56+00:00", "1970-01-01T00:17:06+00:00"),
            ):
                with self.subTest(incident=number):
                    metadata = json.loads((root / str(number) / "incident.json").read_text(encoding="utf-8"))
                    self.assertTrue(metadata["complete"])
                    self.assertEqual(metadata["duration_seconds"], 3)
                    self.assertEqual(metadata["exit_time"], exit_time)
                    self.assertEqual(metadata["closed_at"], closed_at)
                    self.assertNotIn("track_id", metadata)
                    self.assertNotIn("track_removed_at", metadata)
                    self.assertTrue((root / str(number) / "incident.mp4").is_file())
            messages = [call.args[0] for call in message.call_args_list]
            self.assertEqual(sum(text.startswith("Full-frame incident confirmed;") for text in messages), 2)
            self.assertEqual(messages.count("Full-frame incident clip saved."), 2)

    def test_mp4_replay_produces_repeatable_completed_incidents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "input.mp4"
            input_writer = cv2.VideoWriter(str(input_path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (16, 16))
            self.assertTrue(input_writer.isOpened())
            try:
                for _ in range(201):
                    input_writer.write(np.zeros((16, 16, 3), dtype=np.uint8))
            finally:
                input_writer.release()

            timelines = []
            for run in range(2):
                source = VideoFileSource(input_path)
                tracker, renderer = Mock(), Mock()
                person = TrackedDetection(0, 0, 4, 5, 0.9, 7)
                tracker.track.side_effect = [[person]] * 31 + [[]] * 170
                renderer.draw.side_effect = lambda frame, detections: frame.fill(255)
                renderer.show.return_value = True
                recorder = EvidenceRecorder(root / "incidents")
                clock = lambda: (source.position_seconds, 1000 + source.position_seconds)
                with patch("surveillance.application.live_pipeline.monotonic", return_value=run * 10000), patch(
                    "surveillance.application.live_pipeline.time", return_value=run * 10000
                ):
                    LivePipeline(source, tracker, renderer, IncidentTracker(), recorder, clock=clock).run()

                video_path = root / "incidents" / str(run + 1) / "incident.mp4"
                metadata = json.loads(video_path.with_suffix(".json").read_text(encoding="utf-8"))
                self.assertTrue(metadata.pop("complete"))
                self.assertAlmostEqual(metadata["duration_seconds"], 3.1)
                metadata.pop("evidence_clip_path")
                timelines.append(metadata)
                capture = cv2.VideoCapture(str(video_path))
                try:
                    self.assertTrue(capture.isOpened())
                    self.assertEqual(capture.get(cv2.CAP_PROP_FPS), 30)
                    self.assertEqual(capture.get(cv2.CAP_PROP_FRAME_COUNT), 394)
                    ok, frame = capture.read()
                    self.assertTrue(ok)
                    self.assertLess(frame.mean(), 1)
                finally:
                    capture.release()
            self.assertEqual(timelines[0], timelines[1])

    def test_media_clock_preserves_timing_and_incomplete_evidence_at_eof_or_q(self) -> None:
        for stop in ("eof", "q"):
            with self.subTest(stop=stop), tempfile.TemporaryDirectory() as directory:
                source, tracker, renderer = Mock(), Mock(), Mock()
                frame = np.zeros((4, 5, 3), dtype=np.uint8)
                source.read.side_effect = [(True, frame)] * 4 + [(False, None)]
                person = TrackedDetection(0, 0, 4, 5, 0.9, 7)
                tracker.track.return_value = [person]
                renderer.show.side_effect = [True, True, True, stop != "q"]
                writer = Mock()
                recorder = EvidenceRecorder(Path(directory), lambda *args: writer)
                media_clock = iter((second, 1000 + second) for second in range(4))

                with patch("surveillance.application.live_pipeline.monotonic", side_effect=AssertionError("Used processing clock")), patch(
                    "surveillance.application.live_pipeline.time", side_effect=AssertionError("Used processing clock")
                ):
                    LivePipeline(source, tracker, renderer, IncidentTracker(), recorder, clock=media_clock.__next__).run()

                metadata = json.loads((Path(directory) / "1" / "incident.json").read_text(encoding="utf-8"))
                self.assertFalse(metadata["complete"])
                self.assertEqual(metadata["entry_time"], "1970-01-01T00:16:40+00:00")
                self.assertEqual(metadata["confirmation_time"], "1970-01-01T00:16:42+00:00")
                self.assertEqual(writer.write.call_count, 91)
                writer.release.assert_called_once()
                source.close.assert_called_once()
                renderer.close.assert_called_once()

    def test_continuous_sparse_occupancy_through_post_roll_saves_raw_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source, tracker, renderer = Mock(), Mock(), Mock()
            writer = Mock()
            saved_frames = []
            writer.write.side_effect = lambda frame: saved_frames.append(float(frame.mean()))
            times = list(range(-10, 1)) + [3, 4, 14]
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
            self.assertEqual(saved_frames[-1], 24)
            self.assertNotIn(255, saved_frames)
            self.assertEqual(len(saved_frames), 721)
            metadata = json.loads(next(Path(directory).rglob("*.json")).read_text(encoding="utf-8"))
            self.assertTrue(metadata["complete"])
            self.assertEqual(metadata["duration_seconds"], 4)
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

    def test_read_clock_and_render_failures_still_close_every_resource(self) -> None:
        for failure in ("read", "clock", "draw", "show"):
            with self.subTest(failure=failure):
                source, tracker, renderer, incidents, evidence = [Mock() for _ in range(5)]
                source.read.return_value = (True, np.zeros((4, 5, 3), dtype=np.uint8))
                tracker.track.return_value = []
                incidents.update.return_value = ([], [])
                incidents.pending_started_at = None
                clock = Mock(return_value=(1, 1001))
                operation = {
                    "read": source.read, "clock": clock,
                    "draw": renderer.draw, "show": renderer.show,
                }[failure]
                operation.side_effect = RuntimeError(failure)

                with self.assertRaisesRegex(RuntimeError, failure):
                    LivePipeline(source, tracker, renderer, incidents, evidence, clock=clock).run()

                for resource in (source, renderer, evidence):
                    resource.close.assert_called_once()

    def test_display_failure_preserves_active_evidence_as_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source, tracker, renderer = Mock(), Mock(), Mock()
            source.read.return_value = (True, np.zeros((4, 5, 3), dtype=np.uint8))
            tracker.track.return_value = [TrackedDetection(0, 0, 4, 5, 0.9, 7)]
            renderer.show.side_effect = [True, True, RuntimeError("display failed")]
            writer = Mock()
            recorder = EvidenceRecorder(Path(directory), lambda *args: writer)
            clock = iter((second, 1000 + second) for second in range(3))

            with self.assertRaisesRegex(RuntimeError, "display failed"):
                LivePipeline(source, tracker, renderer, IncidentTracker(), recorder, clock=clock.__next__).run()

            metadata = json.loads((Path(directory) / "1" / "incident.json").read_text(encoding="utf-8"))
            self.assertFalse(metadata["complete"])
            writer.release.assert_called_once()
            source.close.assert_called_once()
            renderer.close.assert_called_once()

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
