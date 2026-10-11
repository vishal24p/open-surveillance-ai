import unittest

from surveillance.application.incidents import IncidentTracker
from surveillance.models import TrackedDetection


def person(track_id: int | None) -> TrackedDetection:
    return TrackedDetection(0, 0, 10, 10, 0.9, track_id)


class IncidentTrackerTests(unittest.TestCase):
    def test_fractional_entry_keeps_exact_dwell_boundary(self) -> None:
        tracker = IncidentTracker()
        tracker.update([person(1)], 0.25, 1000.25)
        self.assertEqual(tracker.update([person(1)], 2.249, 1002.249), ([], []))
        confirmed, _ = tracker.update([person(1)], 2.25, 1002.25)
        self.assertEqual(confirmed[0].started_at, 0.25)
        self.assertEqual(confirmed[0].confirmed_at, 2.25)

    def test_empty_frame_at_dwell_boundary_does_not_confirm(self) -> None:
        tracker = IncidentTracker()
        tracker.update([person(1)], 0, 1000)
        self.assertEqual(tracker.update([], 2, 1002), ([], []))
        self.assertIsNone(tracker.pending_started_at)

    def test_repeated_short_visits_never_accumulate_dwell(self) -> None:
        tracker = IncidentTracker()
        for start in (0, 3, 6):
            self.assertEqual(tracker.update([person(None)], start, 1000 + start), ([], []))
            self.assertEqual(tracker.update([], start + 1.5, 1001.5 + start), ([], []))
        self.assertIsNone(tracker.pending_started_at)

    def test_repeated_occupied_updates_emit_confirmation_only_once(self) -> None:
        tracker = IncidentTracker()
        tracker.update([person(1)], 0, 1000)
        confirmed, _ = tracker.update([person(1)], 2, 1002)
        self.assertEqual(len(confirmed), 1)
        for now in (2, 2.1, 50):
            self.assertEqual(tracker.update([person(None)], now, 1000 + now), ([], []))

    def test_fractional_empty_deadline_closes_at_exact_boundary(self) -> None:
        tracker = IncidentTracker()
        tracker.update([person(1)], 0, 1000)
        tracker.update([person(1)], 2, 1002)
        tracker.update([], 3.25, 1003.25)
        self.assertEqual(tracker.update([], 13.249, 1013.249), ([], []))
        _, completed = tracker.update([], 13.25, 1013.25)
        self.assertEqual(completed[0].closed_at, 13.25)
        self.assertEqual(completed[0].duration_seconds, 3.25)

    def test_late_poll_preserves_original_exit_and_deadline_epochs(self) -> None:
        tracker = IncidentTracker()
        tracker.update([person(1)], 0, 1000)
        tracker.update([person(1)], 2, 1002)
        tracker.update([], 3, 1003)
        _, completed = tracker.update([], 99, 9999)
        self.assertEqual(completed[0].exit_epoch, 1003)
        self.assertEqual(completed[0].closed_epoch, 1013)
        self.assertEqual(completed[0].closed_at, 13)

    def test_multiple_returns_extend_same_incident_until_final_empty_period(self) -> None:
        tracker = IncidentTracker()
        tracker.update([person(1)], 0, 1000)
        confirmed, _ = tracker.update([person(1)], 2, 1002)
        for now, detections in ((3, []), (12, [person(None)]), (13, []), (22, [person(9)]), (23, [])):
            self.assertEqual(tracker.update(detections, now, 1000 + now), ([], []))
        _, completed = tracker.update([], 33, 1033)
        self.assertEqual(completed[0].incident, confirmed[0])
        self.assertEqual(completed[0].exit_at, 23)
        self.assertEqual(completed[0].duration_seconds, 23)

    def test_wall_clock_jump_does_not_change_dwell_or_post_roll(self) -> None:
        tracker = IncidentTracker()
        tracker.update([person(1)], 0, 1000)
        confirmed, _ = tracker.update([person(1)], 2, 500)
        self.assertEqual(confirmed[0].confirmed_epoch, 500)
        tracker.update([], 3, 501)
        _, completed = tracker.update([], 13, 9000)
        self.assertEqual(completed[0].closed_epoch, 511)
        self.assertEqual(completed[0].duration_seconds, 3)

    def test_confirms_after_two_occupied_seconds(self) -> None:
        tracker = IncidentTracker()
        self.assertIsNone(tracker.pending_started_at)
        self.assertEqual(tracker.update([person(1)], 0, 1000), ([], []))
        self.assertEqual(tracker.pending_started_at, 0)
        self.assertEqual(tracker.update([person(1)], 1.99, 1001.99), ([], []))

        confirmed, completed = tracker.update([person(1)], 2, 1002)

        self.assertEqual(len(confirmed), 1)
        self.assertEqual(confirmed[0].started_at, 0)
        self.assertEqual(confirmed[0].confirmed_at, 2)
        self.assertEqual(confirmed[0].started_epoch, 1000)
        self.assertEqual(confirmed[0].confirmed_epoch, 1002)
        self.assertEqual(completed, [])
        self.assertIsNone(tracker.pending_started_at)

    def test_id_handoff_preserves_pending_frame_dwell(self) -> None:
        tracker = IncidentTracker()
        tracker.update([person(1)], 0, 1000)
        tracker.update([person(2)], 1, 1001)

        confirmed, _ = tracker.update([person(3)], 2, 1002)

        self.assertEqual(len(confirmed), 1)
        self.assertEqual(confirmed[0].started_at, 0)
        self.assertIsNone(tracker.pending_started_at)

    def test_untracked_person_counts_as_frame_occupancy(self) -> None:
        tracker = IncidentTracker()
        tracker.update([person(None)], 0, 1000)

        confirmed, _ = tracker.update([person(None)], 2, 1002)

        self.assertEqual(len(confirmed), 1)
        self.assertEqual(confirmed[0].started_at, 0)

    def test_empty_frame_resets_unconfirmed_dwell(self) -> None:
        tracker = IncidentTracker()
        tracker.update([person(1)], 0, 1000)
        self.assertEqual(tracker.update([], 1, 1001), ([], []))
        self.assertIsNone(tracker.pending_started_at)
        self.assertEqual(tracker.update([person(1)], 2, 1002), ([], []))
        self.assertEqual(tracker.pending_started_at, 2)
        self.assertEqual(tracker.update([person(1)], 3.99, 1003.99), ([], []))

        confirmed, _ = tracker.update([person(1)], 4, 1004)

        self.assertEqual(confirmed[0].started_at, 2)

    def test_multiple_people_and_partial_departures_keep_one_incident(self) -> None:
        tracker = IncidentTracker()
        tracker.update([person(1), person(2)], 0, 1000)
        confirmed, _ = tracker.update([person(1), person(2)], 2, 1002)
        self.assertEqual(len(confirmed), 1)

        for timestamp, ids in ((5, [1, 2, 3]), (10, [1, 2]), (20, [2]), (30, [4])):
            with self.subTest(timestamp=timestamp):
                self.assertEqual(
                    tracker.update([person(track_id) for track_id in ids], timestamp, 1000 + timestamp),
                    ([], []),
                )

    def test_closes_after_ten_empty_seconds_from_first_empty_frame(self) -> None:
        tracker = IncidentTracker()
        tracker.update([person(1)], 0, 1000)
        confirmed, _ = tracker.update([person(1)], 2, 1002)
        self.assertEqual(tracker.update([], 5, 1005), ([], []))
        self.assertEqual(tracker.update([], 14.99, 1014.99), ([], []))

        newly_confirmed, completed = tracker.update([], 15, 1015)

        self.assertEqual(newly_confirmed, [])
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0].incident, confirmed[0])
        self.assertEqual(completed[0].exit_at, 5)
        self.assertEqual(completed[0].exit_epoch, 1005)
        self.assertEqual(completed[0].closed_at, 15)
        self.assertEqual(completed[0].closed_epoch, 1015)
        self.assertEqual(completed[0].duration_seconds, 5)
        self.assertEqual(tracker.update([], 16, 1016), ([], []))

    def test_any_person_return_before_deadline_continues_and_resets_empty_timer(self) -> None:
        tracker = IncidentTracker()
        tracker.update([person(1)], 0, 1000)
        confirmed, _ = tracker.update([person(1)], 2, 1002)
        tracker.update([], 3, 1003)
        self.assertEqual(tracker.update([person(9)], 12.99, 1012.99), ([], []))
        self.assertEqual(tracker.update([], 15, 1015), ([], []))
        self.assertEqual(tracker.update([], 24.99, 1024.99), ([], []))

        _, completed = tracker.update([], 25, 1025)

        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0].incident, confirmed[0])
        self.assertEqual(completed[0].exit_at, 15)
        self.assertEqual(completed[0].closed_at, 25)
        self.assertEqual(completed[0].duration_seconds, 15)

    def test_return_at_or_after_deadline_completes_old_and_starts_new_dwell(self) -> None:
        for returned_at in (13, 20):
            with self.subTest(returned_at=returned_at):
                tracker = IncidentTracker()
                tracker.update([person(1)], 0, 1000)
                first, _ = tracker.update([person(1)], 2, 1002)
                tracker.update([], 3, 1003)

                confirmed, completed = tracker.update([person(1)], returned_at, 1000 + returned_at)

                self.assertEqual(confirmed, [])
                self.assertEqual(len(completed), 1)
                self.assertEqual(completed[0].incident, first[0])
                self.assertEqual(completed[0].closed_at, 13)
                self.assertEqual(tracker.pending_started_at, returned_at)
                self.assertEqual(tracker.update([person(2)], returned_at + 1.99, 1001.99 + returned_at), ([], []))
                second, completed = tracker.update([person(2)], returned_at + 2, 1002 + returned_at)
                self.assertEqual(len(second), 1)
                self.assertEqual(second[0].started_at, returned_at)
                self.assertEqual(completed, [])

    def test_empty_scene_never_creates_an_incident(self) -> None:
        tracker = IncidentTracker()
        for timestamp in (0, 2, 30):
            self.assertEqual(tracker.update([], timestamp, 1000 + timestamp), ([], []))
            self.assertIsNone(tracker.pending_started_at)


if __name__ == "__main__":
    unittest.main()
