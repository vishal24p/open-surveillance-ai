import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import cv2

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
    def test_failed_frame_encoding_does_not_poison_later_recording(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = FakeVideoWriter()
            recorder = EvidenceRecorder(Path(directory), lambda *args: writer)
            self.addCleanup(recorder.close)
            frame = np.zeros((4, 5, 3), dtype=np.uint8)
            with patch("surveillance.application.evidence.cv2.imencode", return_value=(False, None)):
                with self.assertRaisesRegex(RuntimeError, "encode frame"):
                    recorder.buffer_frame(frame, 0)
            recorder.buffer_frame(frame, 2)
            recorder.start_incident(ConfirmedIncident(0, 2, 100, 102))
            self.assertEqual(len(writer.frames), 1)
            recorder.close()

    def test_abandoned_pending_visit_stops_retaining_old_pre_roll(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = FakeVideoWriter()
            recorder = EvidenceRecorder(Path(directory), lambda *args: writer)
            self.addCleanup(recorder.close)
            for timestamp, value, pending in ((0, 0, 0), (20, 20, 0), (30, 30, None)):
                recorder.buffer_frame(np.full((4, 5, 3), value, dtype=np.uint8), timestamp, pending)
                if timestamp == 20:
                    self.assertEqual([time for time, _ in recorder._history], [0, 20])
            self.assertEqual([time for time, _ in recorder._history], [20, 30])
            recorder.start_incident(ConfirmedIncident(30, 32, 130, 132))
            self.assertEqual(float(writer.frames[0].mean()), 20)
            recorder.close()

    def test_recovery_after_failed_writer_open_uses_next_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            failed, recovered = FakeVideoWriter(), FakeVideoWriter()
            recorder = EvidenceRecorder(Path(directory), Mock(side_effect=[failed, recovered]))
            self.addCleanup(recorder.close)
            recorder.buffer_frame(np.zeros((4, 5, 3), dtype=np.uint8), 2)
            incident = ConfirmedIncident(0, 2, 100, 102)
            with patch.object(failed, "isOpened", return_value=False):
                with self.assertRaises(RuntimeError):
                    recorder.start_incident(incident)
            path = recorder.start_incident(incident)
            self.assertEqual(path.parent.name, "2")
            self.assertFalse(json.loads((Path(directory) / "1" / "incident.json").read_text())["complete"])
            self.assertEqual(len(recovered.frames), 1)
            recorder.close()

    def test_post_roll_poll_after_deadline_holds_last_frame_without_new_scene(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = FakeVideoWriter()
            recorder = EvidenceRecorder(Path(directory), lambda *args: writer)
            self.addCleanup(recorder.close)
            recorder.buffer_frame(np.zeros((4, 5, 3), dtype=np.uint8), 0)
            incident = ConfirmedIncident(0, 2, 100, 102)
            recorder.start_incident(incident)
            recorder.write_active_frame(np.full((4, 5, 3), 20, dtype=np.uint8), 3, [])
            completed = CompletedIncident(incident, 3, 103, 13, 113, 3)
            recorder.write_active_frame(np.full((4, 5, 3), 255, dtype=np.uint8), 20, [completed])
            recorder.finish_incident(completed)
            self.assertEqual(len(writer.frames), 391)
            self.assertEqual(float(writer.frames[-1].mean()), 20)
            self.assertFalse(any(frame.mean() == 255 for frame in writer.frames))

    def test_completed_metadata_survives_repeated_close(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = FakeVideoWriter()
            recorder = EvidenceRecorder(Path(directory), lambda *args: writer)
            recorder.buffer_frame(np.zeros((4, 5, 3), dtype=np.uint8), 0)
            incident = ConfirmedIncident(0, 2, 100, 102)
            path = recorder.start_incident(incident)
            recorder.finish_incident(CompletedIncident(incident, 3, 103, 13, 113, 3))
            original = path.with_suffix(".json").read_bytes()
            with patch.object(writer, "release") as release:
                recorder.close()
                recorder.close()
            release.assert_not_called()
            self.assertEqual(path.with_suffix(".json").read_bytes(), original)

    def test_subframe_capture_updates_image_held_during_next_gap(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = FakeVideoWriter()
            recorder = EvidenceRecorder(Path(directory), lambda *args: writer)
            self.addCleanup(recorder.close)
            recorder.buffer_frame(np.zeros((4, 5, 3), dtype=np.uint8), 0)
            recorder.start_incident(ConfirmedIncident(0, 2, 100, 102))
            recorder.write_active_frame(np.full((4, 5, 3), 40, dtype=np.uint8), 0.01, [])
            self.assertEqual(len(writer.frames), 1)
            recorder.write_active_frame(np.full((4, 5, 3), 80, dtype=np.uint8), 0.1, [])
            self.assertEqual([float(frame.mean()) for frame in writer.frames], [0, 40, 40, 80])
            recorder.close()

    def test_incomplete_metadata_contains_only_available_times(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            recorder = EvidenceRecorder(Path(directory), FakeVideoWriter)
            recorder.buffer_frame(np.zeros((4, 5, 3), dtype=np.uint8), 0)
            path = recorder.start_incident(ConfirmedIncident(0, 2, 100.25, 102.5))
            recorder.close()
            metadata = json.loads(path.with_suffix(".json").read_text())
            self.assertEqual(metadata["entry_time"], "1970-01-01T00:01:40.250000+00:00")
            self.assertEqual(metadata["confirmation_time"], "1970-01-01T00:01:42.500000+00:00")
            self.assertNotIn("exit_time", metadata)
            self.assertNotIn("closed_at", metadata)
            self.assertNotIn("duration_seconds", metadata)

    def test_startup_failures_keep_incomplete_metadata(self) -> None:
        for failure in ("no_frames", "first_decode", "later_decode", "writer_open", "writer_creation", "write"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                frame = np.zeros((16, 16, 3), dtype=np.uint8)
                writer = FakeVideoWriter()
                factory = Mock(return_value=writer)
                recorder = EvidenceRecorder(Path(directory), factory)
                if failure != "no_frames":
                    recorder.buffer_frame(frame, 0)
                    recorder.buffer_frame(frame, 2)
                if failure == "writer_creation":
                    factory.side_effect = RuntimeError("writer creation failed")
                decoded_frames = [frame, frame]
                if failure == "first_decode":
                    decoded_frames = [RuntimeError("decode failed")]
                elif failure == "later_decode":
                    decoded_frames = [frame, RuntimeError("decode failed")]
                with patch.object(recorder, "_decode_frame", side_effect=decoded_frames):
                    with patch.object(writer, "isOpened", return_value=failure != "writer_open"), patch.object(writer, "write", side_effect=RuntimeError("write failed") if failure == "write" else None):
                        with self.assertRaises(RuntimeError):
                            recorder.start_incident(ConfirmedIncident(0, 2, 100, 102))
                recorder.close()
                metadata = json.loads((Path(directory) / "1" / "incident.json").read_text())
                self.assertNotIn("track_id", metadata)
                self.assertFalse(metadata["complete"])
                if failure in ("later_decode", "writer_open", "write"):
                    self.assertTrue(writer.released)

    def test_active_incident_has_incomplete_metadata_before_close(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            recorder = EvidenceRecorder(Path(directory), FakeVideoWriter)
            recorder.buffer_frame(np.zeros((16, 16, 3), dtype=np.uint8), 0)
            path = recorder.start_incident(ConfirmedIncident(0, 2, 100, 102))
            try:
                self.assertFalse(json.loads(path.with_suffix(".json").read_text())["complete"])
            finally:
                recorder.close()

    def test_finalization_failures_keep_incomplete_metadata_and_cleanup(self) -> None:
        for failure in ("write", "release", "metadata"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                writer = FakeVideoWriter()
                recorder = EvidenceRecorder(Path(directory), lambda *args: writer)
                recorder.buffer_frame(np.zeros((16, 16, 3), dtype=np.uint8), 0)
                incident = ConfirmedIncident(0, 2, 100, 102)
                path = recorder.start_incident(incident)
                completed = CompletedIncident(incident, 3, 103, 13, 113, 3)
                target, method = (recorder, "_write_metadata") if failure == "metadata" else (writer, failure)
                with patch.object(target, method, side_effect=OSError("saving failed")):
                    with self.assertRaises(OSError):
                        recorder.finish_incident(completed)
                recorder.close()
                self.assertTrue(writer.released)
                self.assertFalse(json.loads(path.with_suffix(".json").read_text())["complete"])

    def test_failed_metadata_replacement_preserves_previous_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "incident.mp4"
            EvidenceRecorder._write_metadata(path, {"complete": False})
            original = path.with_suffix(".json").read_bytes()
            with patch.object(Path, "replace", side_effect=OSError("replace failed")):
                with self.assertRaises(OSError):
                    EvidenceRecorder._write_metadata(path, {"complete": True})
            self.assertEqual(path.with_suffix(".json").read_bytes(), original)
            self.assertFalse(path.with_suffix(".json.tmp").exists())

    def test_completed_mp4_is_playable_with_elapsed_frame_count(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            recorder = EvidenceRecorder(Path(directory))
            for timestamp in (0, 1, 2):
                recorder.buffer_frame(np.full((16, 16, 3), timestamp * 50, dtype=np.uint8), timestamp)
            incident = ConfirmedIncident(0, 2, 100, 102)
            path = recorder.start_incident(incident)
            recorder.finish_incident(CompletedIncident(incident, 3, 103, 13, 113, 3))
            capture = cv2.VideoCapture(str(path))
            try:
                count = 0
                while capture.read()[0]:
                    count += 1
                self.assertEqual(count, 391)
                self.assertAlmostEqual(capture.get(cv2.CAP_PROP_FPS), 30)
                self.assertTrue(json.loads(path.with_suffix(".json").read_text())["complete"])
            finally:
                capture.release()
                recorder.close()

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

            video_path = recorder.start_incident(ConfirmedIncident(0, 2, 100, 102))
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
                recorder.start_incident(ConfirmedIncident(0, 2, 100, 102))
                self.assertEqual(len(writer.frames), 61)
                recorder.close()

    def test_close_releases_writer_after_metadata_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = FakeVideoWriter()
            recorder = EvidenceRecorder(Path(directory), lambda *args: writer)
            recorder.buffer_frame(np.zeros((4, 5, 3), dtype=np.uint8), 2)
            path = recorder.start_incident(ConfirmedIncident(0, 2, 100, 102))
            with patch.object(recorder, "_write_metadata", side_effect=OSError("disk full")):
                with self.assertRaisesRegex(OSError, "disk full"):
                    recorder.close()
            self.assertTrue(writer.released)
            self.assertFalse(json.loads(path.with_suffix(".json").read_text())["complete"])
            self.assertIsNone(recorder._writer)

    def test_close_saves_incomplete_metadata_even_when_release_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = FakeVideoWriter()
            recorder = EvidenceRecorder(Path(directory), lambda *args: writer)
            recorder.buffer_frame(np.zeros((4, 5, 3), dtype=np.uint8), 0)
            path = recorder.start_incident(ConfirmedIncident(0, 2, 100, 102))
            with patch.object(writer, "release", side_effect=OSError("release failed")):
                with self.assertRaisesRegex(OSError, "release failed"):
                    recorder.close()
            self.assertFalse(json.loads(path.with_suffix(".json").read_text())["complete"])

    def test_second_start_cannot_abandon_active_writer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = FakeVideoWriter()
            recorder = EvidenceRecorder(Path(directory), lambda *args: writer)
            recorder.buffer_frame(np.zeros((4, 5, 3), dtype=np.uint8), 0)
            path = recorder.start_incident(ConfirmedIncident(0, 2, 100, 102))
            try:
                with self.assertRaisesRegex(RuntimeError, "already"):
                    recorder.start_incident(ConfirmedIncident(3, 5, 103, 105))
                self.assertEqual(len(list(Path(directory).iterdir())), 1)
            finally:
                recorder.close()
            self.assertTrue(writer.released)
            self.assertFalse(json.loads(path.with_suffix(".json").read_text())["complete"])

    def test_sequential_incidents_keep_separate_clips_without_person_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            recorder = EvidenceRecorder(Path(directory), FakeVideoWriter)
            frame = np.zeros((4, 5, 3), dtype=np.uint8)
            paths = []
            for start in (0, 20):
                recorder.buffer_frame(frame, start)
                incident = ConfirmedIncident(start, start + 2, 100 + start, 102 + start)
                paths.append(recorder.start_incident(incident))
                recorder.finish_incident(CompletedIncident(incident, start + 3, 103 + start, start + 13, 113 + start, 3))
            recorder.close()
            self.assertEqual([path.parent.name for path in paths], ["1", "2"])
            for path in paths:
                metadata = json.loads(path.with_suffix(".json").read_text())
                self.assertTrue(metadata["complete"])
                self.assertEqual(metadata["zone"], "full_frame")
                self.assertNotIn("track_id", metadata)
                self.assertNotIn("track_removed_at", metadata)

    def test_failed_writer_open_releases_handle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = FakeVideoWriter()
            recorder = EvidenceRecorder(Path(directory), lambda *args: writer)
            recorder.buffer_frame(np.zeros((4, 5, 3), dtype=np.uint8), 2)
            with patch.object(writer, "isOpened", return_value=False):
                with self.assertRaisesRegex(RuntimeError, "Could not create incident video"):
                    recorder.start_incident(ConfirmedIncident(0, 2, 100, 102))
            self.assertTrue(writer.released)
            self.assertIsNone(recorder._writer)

    def test_failed_decode_releases_started_writer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            frame = np.zeros((4, 5, 3), dtype=np.uint8)
            writer = FakeVideoWriter()
            recorder = EvidenceRecorder(Path(directory), lambda *args: writer)
            recorder.buffer_frame(frame, 0)
            recorder.buffer_frame(frame, 2)
            with patch("surveillance.application.evidence.cv2.imdecode", side_effect=[frame, None]):
                with self.assertRaisesRegex(RuntimeError, "Could not decode frame"):
                    recorder.start_incident(ConfirmedIncident(0, 2, 100, 102))
            self.assertTrue(writer.released)
            self.assertIsNone(recorder._writer)

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

            incident = ConfirmedIncident(20, 22, 1_700_000_000, 1_700_000_002)
            video_path = recorder.start_incident(incident)
            self.assertEqual(video_path.parent.name, "1")
            self.assertEqual(video_path.name, "incident.mp4")
            self.assertEqual(len(writers[0].frames), 361)
            self.assertAlmostEqual(float(writers[0].frames[0].mean()), 10, delta=1)

            completed = CompletedIncident(
                incident=incident,
                exit_at=26,
                exit_epoch=1_700_000_006,
                closed_at=36,
                closed_epoch=1_700_000_016,
                duration_seconds=6,
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
            self.assertNotIn("track_id", metadata)
            self.assertEqual(metadata["duration_seconds"], 6)
            self.assertTrue(metadata["complete"])

    def test_delayed_confirmation_keeps_candidate_pre_roll(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = FakeVideoWriter()
            recorder = EvidenceRecorder(Path(directory), lambda *args: writer)
            for timestamp in range(-10, 1):
                recorder.buffer_frame(np.full((4, 5, 3), timestamp + 10, dtype=np.uint8), timestamp)
            recorder.buffer_frame(np.full((4, 5, 3), 13, dtype=np.uint8), 3, 0)
            recorder.start_incident(ConfirmedIncident(0, 3, 100, 103))

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
            recorder.start_incident(ConfirmedIncident(0, 2, 100, 102))
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
            recorder.start_incident(ConfirmedIncident(0, 2, 100, 102))
            self.assertEqual(len(writer.frames), 61)
            recorder.close()


if __name__ == "__main__":
    unittest.main()
