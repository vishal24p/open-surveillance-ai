import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

from surveillance.application.evidence import EvidenceRecorder
from surveillance.application.incidents import CompletedIncident, ConfirmedIncident


class FakeVideoWriter:
    def __init__(self, *args) -> None:
        self.frames = []
        self.released = False
        self.args = args

    def isOpened(self) -> bool:
        return True

    def write(self, frame) -> None:
        self.frames.append(frame.copy())

    def release(self) -> None:
        self.released = True


class EvidenceRecorderTests(unittest.TestCase):
    def test_fresh_recorder_preserves_existing_incident_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            existing_dir = output_dir / "1"
            existing_dir.mkdir()
            existing_video = existing_dir / "incident.mp4"
            existing_metadata = existing_dir / "incident.json"
            existing_video.write_bytes(b"previous incident video")
            existing_metadata.write_bytes(b'{"track_id": 7, "complete": true}')
            writer = FakeVideoWriter()
            factory = Mock(return_value=writer)
            recorder = EvidenceRecorder(output_dir, factory)
            recorder.buffer_frame(np.zeros((4, 5, 3), dtype=np.uint8), 2)

            video_path = recorder.start_incident(ConfirmedIncident(7, 0, 2, 100, 102))
            recorder.close()

            self.assertEqual(video_path, output_dir / "2" / "incident.mp4")
            self.assertEqual(factory.call_args.args[0], str(video_path))
            self.assertTrue(video_path.with_suffix(".json").is_file())
            self.assertEqual(existing_video.read_bytes(), b"previous incident video")
            self.assertEqual(existing_metadata.read_bytes(), b'{"track_id": 7, "complete": true}')

    def test_pre_roll_decodes_one_frame_before_writer_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            frame = np.zeros((4, 5, 3), dtype=np.uint8)
            writer = FakeVideoWriter()
            with patch("surveillance.application.evidence.cv2.imdecode", return_value=frame) as decode:
                def create_writer(*args):
                    self.assertEqual(decode.call_count, 1)
                    return writer

                recorder = EvidenceRecorder(Path(directory), create_writer)
                for timestamp in range(3):
                    recorder.buffer_frame(frame, timestamp)
                recorder.start_incident(ConfirmedIncident(7, 0, 2, 100, 102))
                self.assertEqual(len(writer.frames), 61)
                recorder.close()

    def test_close_releases_all_writers_after_metadata_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writers = [FakeVideoWriter(), FakeVideoWriter()]
            recorder = EvidenceRecorder(Path(directory), lambda *args: writers[len(recorder._writers)])
            recorder.buffer_frame(np.zeros((4, 5, 3), dtype=np.uint8), 2)
            for track_id in (7, 8):
                recorder.start_incident(ConfirmedIncident(track_id, 0, 2, 100, 102))
            error = OSError("disk full")
            with patch.object(recorder, "_write_metadata", side_effect=[error, None]) as metadata:
                with self.assertRaises(OSError) as raised:
                    recorder.close()
                self.assertIs(raised.exception, error)
                self.assertEqual(metadata.call_count, 2)
            self.assertTrue(all(writer.released for writer in writers))
            self.assertEqual(recorder._writers, {})

    def test_failed_writer_open_releases_handle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = FakeVideoWriter()
            recorder = EvidenceRecorder(Path(directory), lambda *args: writer)
            recorder.buffer_frame(np.zeros((4, 5, 3), dtype=np.uint8), 2)
            with patch.object(writer, "isOpened", return_value=False):
                with self.assertRaisesRegex(RuntimeError, "Could not create incident video"):
                    recorder.start_incident(ConfirmedIncident(7, 0, 2, 100, 102))
            self.assertTrue(writer.released)
            self.assertEqual(recorder._writers, {})

    def test_failed_decode_releases_started_writer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            frame = np.zeros((4, 5, 3), dtype=np.uint8)
            writer = FakeVideoWriter()
            recorder = EvidenceRecorder(Path(directory), lambda *args: writer)
            recorder.buffer_frame(frame, 0)
            recorder.buffer_frame(frame, 2)
            with patch("surveillance.application.evidence.cv2.imdecode", side_effect=[frame, None]):
                with self.assertRaisesRegex(RuntimeError, "Could not decode frame"):
                    recorder.start_incident(ConfirmedIncident(7, 0, 2, 100, 102))
            self.assertTrue(writer.released)
            self.assertEqual(recorder._writers, {})

    def test_clip_contains_ten_seconds_before_detection_and_until_post_roll_end(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writers = []

            def create_writer(*args):
                writer = FakeVideoWriter(*args)
                writers.append(writer)
                return writer

            recorder = EvidenceRecorder(Path(directory), create_writer)
            for timestamp in range(23):
                frame = np.full((4, 5, 3), timestamp, dtype=np.uint8)
                recorder.buffer_frame(frame, timestamp)

            incident = ConfirmedIncident(7, 20, 22, 1_700_000_000, 1_700_000_002)
            video_path = recorder.start_incident(incident)
            self.assertEqual(video_path.parent.name, "1")
            self.assertEqual(video_path.name, "incident.mp4")
            self.assertEqual(len(writers[0].frames), 361)
            self.assertAlmostEqual(float(writers[0].frames[0].mean()), 10, delta=1)

            completed = CompletedIncident(
                incident=incident,
                exit_at=25,
                exit_epoch=1_700_000_005,
                removed_at=26,
                removed_epoch=1_700_000_006,
                closed_at=36,
                closed_epoch=1_700_000_016,
                duration_seconds=5,
            )
            for timestamp in range(23, 38):
                frame = np.full((4, 5, 3), timestamp, dtype=np.uint8)
                recorder.buffer_frame(frame, timestamp)
                recorder.write_active_frame(frame, timestamp, [completed] if timestamp >= 36 else [])
            recorder.finish_incident(completed)

            self.assertEqual(len(writers[0].frames), 781)
            self.assertEqual(float(writers[0].frames[-1].mean()), 36)
            self.assertTrue(writers[0].released)
            metadata = json.loads(video_path.with_suffix(".json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["zone"], "full_frame")
            self.assertEqual(metadata["track_id"], 7)
            self.assertEqual(metadata["duration_seconds"], 5)
            self.assertTrue(metadata["complete"])

    def test_delayed_confirmation_keeps_candidate_pre_roll(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = FakeVideoWriter()
            recorder = EvidenceRecorder(Path(directory), lambda *args: writer)
            for timestamp in range(-10, 1):
                recorder.buffer_frame(np.full((4, 5, 3), timestamp + 10, dtype=np.uint8), timestamp)
            recorder.buffer_frame(np.full((4, 5, 3), 13, dtype=np.uint8), 3, 0)
            recorder.start_incident(ConfirmedIncident(7, 0, 3, 100, 103))

            self.assertEqual(float(writer.frames[0].mean()), 0)
            self.assertEqual(len(writer.frames), 391)
            recorder.buffer_frame(np.zeros((4, 5, 3), dtype=np.uint8), 20)
            self.assertTrue(all(timestamp >= 7.5 for timestamp, _ in recorder._history))
            recorder.close()

    def test_changing_cadence_preserves_elapsed_playback_time(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = FakeVideoWriter()
            factory = Mock(return_value=writer)
            recorder = EvidenceRecorder(Path(directory), factory)
            for index in range(21):
                recorder.buffer_frame(np.full((4, 5, 3), index, dtype=np.uint8), index / 10)
            recorder.start_incident(ConfirmedIncident(7, 0, 2, 100, 102))
            for timestamp in range(3, 13):
                recorder.write_active_frame(np.full((4, 5, 3), timestamp * 10, dtype=np.uint8), timestamp, [])

            self.assertEqual(factory.call_args.args[2], 30)
            self.assertEqual(len(writer.frames), 361)
            self.assertEqual(float(writer.frames[75].mean()), 20)
            self.assertEqual(float(writer.frames[90].mean()), 30)
            self.assertEqual(float(writer.frames[-1].mean()), 120)
            recorder.close()

    def test_frames_above_output_rate_do_not_extend_playback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = FakeVideoWriter()
            recorder = EvidenceRecorder(Path(directory), lambda *args: writer)
            frame = np.zeros((4, 5, 3), dtype=np.uint8)
            for index in range(121):
                recorder.buffer_frame(frame, index / 60)
            recorder.start_incident(ConfirmedIncident(7, 0, 2, 100, 102))
            self.assertEqual(len(writer.frames), 61)
            recorder.close()


if __name__ == "__main__":
    unittest.main()
