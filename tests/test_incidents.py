import unittest

from surveillance.application.incidents import IncidentTracker
from surveillance.models import TrackedDetection


def person(track_id: int) -> TrackedDetection:
    return TrackedDetection(0, 0, 10, 10, 0.9, track_id)


class IncidentTrackerTests(unittest.TestCase):
    def test_pending_entry_tracks_earliest_unconfirmed_person(self) -> None:
        tracker = IncidentTracker()
        self.assertIsNone(tracker.pending_started_at)
        tracker.update([person(1)], 0, 1000)
        tracker.update([person(1), person(2)], 1, 1001)
        self.assertEqual(tracker.pending_started_at, 0)
        tracker.update([person(1), person(2)], 2, 1002)
        self.assertEqual(tracker.pending_started_at, 1)
        tracker.update([person(1), person(2)], 3, 1003)
        self.assertIsNone(tracker.pending_started_at)

    def test_pending_entry_is_released_after_grace_expires(self) -> None:
        tracker = IncidentTracker()
        tracker.update([person(1)], 0, 1000)
        for frame in range(1, 31):
            tracker.update([], frame / 30, 1000 + frame / 30)
        self.assertEqual(tracker.pending_started_at, 0)
        tracker.update([], 31 / 30, 1000 + 31 / 30)
        self.assertIsNone(tracker.pending_started_at)

    def test_return_after_thirty_misses_preserves_dwell(self) -> None:
        tracker = IncidentTracker()
        tracker.update([person(1)], 0, 1000)
        tracker.update([person(1)], 0.5, 1000.5)
        for frame in range(1, 31):
            tracker.update([], 0.5 + frame / 30, 1000.5 + frame / 30)

        confirmed, completed = tracker.update([person(1)], 2, 1002)

        self.assertEqual(len(confirmed), 1)
        self.assertEqual(confirmed[0].started_at, 0)
        self.assertEqual(completed, [])

    def test_return_after_thirty_one_misses_starts_fresh_dwell(self) -> None:
        tracker = IncidentTracker()
        tracker.update([person(1)], 0, 1000)
        for frame in range(1, 32):
            tracker.update([], frame / 30, 1000 + frame / 30)

        self.assertEqual(tracker.update([person(1)], 2, 1002), ([], []))
        confirmed, _ = tracker.update([person(1)], 4, 1004)
        self.assertEqual(confirmed[0].started_at, 2)

    def test_multiple_tracks_confirm_independently(self) -> None:
        tracker = IncidentTracker()
        tracker.update([person(1)], 0, 1000)
        tracker.update([person(1), person(2)], 1, 1001)

        confirmed, _ = tracker.update([person(1), person(2)], 2, 1002)
        self.assertEqual([incident.track_id for incident in confirmed], [1])
        confirmed, _ = tracker.update([person(1), person(2)], 3, 1003)
        self.assertEqual([incident.track_id for incident in confirmed], [2])

    def test_return_after_expired_post_roll_requires_new_dwell(self) -> None:
        tracker = IncidentTracker()
        tracker.update([person(1)], 0, 1000)
        tracker.update([person(1)], 2, 1002)
        for frame in range(1, 32):
            tracker.update([], 2 + frame / 30, 1002 + frame / 30)

        confirmed, completed = tracker.update([person(1)], 14, 1014)
        self.assertEqual(confirmed, [])
        self.assertEqual(len(completed), 1)
        self.assertAlmostEqual(completed[0].removed_at, 2 + 31 / 30)
        confirmed, _ = tracker.update([person(1)], 16, 1016)
        self.assertEqual(confirmed[0].started_at, 14)

    def test_confirms_after_two_seconds_and_closes_ten_seconds_after_final_exit(self) -> None:
        tracker = IncidentTracker()

        self.assertEqual(tracker.update([person(7)], 0, 1000), ([], []))
        confirmed, _ = tracker.update([person(7)], 1.99, 1001.99)
        self.assertEqual(confirmed, [])
        confirmed, _ = tracker.update([person(7)], 2, 1002)
        self.assertEqual(confirmed[0].started_at, 0)
        self.assertEqual(confirmed[0].confirmed_at, 2)
        tracker.update([person(7)], 6, 1006)

        for frame in range(1, 32):
            _, completed = tracker.update([], 6 + frame / 30, 1006 + frame / 30)
        self.assertEqual(completed, [])

        _, completed = tracker.update([], 17 + 1 / 30, 1017 + 1 / 30)
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0].exit_at, 6)
        self.assertEqual(completed[0].duration_seconds, 6)
        self.assertAlmostEqual(completed[0].closed_at, 17 + 1 / 30)

    def test_same_track_return_during_post_roll_continues_incident_and_resets_timer(self) -> None:
        tracker = IncidentTracker()
        tracker.update([person(4)], 0, 1000)
        tracker.update([person(4)], 2, 1002)

        for frame in range(1, 32):
            tracker.update([], 2 + frame / 30, 1002 + frame / 30)

        confirmed, completed = tracker.update([person(4)], 5, 1005)
        self.assertEqual(confirmed, [])
        self.assertEqual(completed, [])

        for frame in range(1, 32):
            _, completed = tracker.update([], 5 + frame / 30, 1005 + frame / 30)
        self.assertEqual(completed, [])

        _, completed = tracker.update([], 16 + 1 / 30, 1016 + 1 / 30)
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0].exit_at, 5)
        self.assertAlmostEqual(completed[0].closed_at, 16 + 1 / 30)

    def test_short_appearance_never_confirms_an_incident(self) -> None:
        tracker = IncidentTracker()
        tracker.update([person(2)], 0, 1000)
        for frame in range(1, 31):
            confirmed, completed = tracker.update([], frame / 30, 1000 + frame / 30)
            self.assertEqual(confirmed, [])
            self.assertEqual(completed, [])

    def test_untracked_detection_does_not_start_an_incident(self) -> None:
        tracker = IncidentTracker()
        detection = TrackedDetection(0, 0, 10, 10, 0.9, None)

        confirmed, completed = tracker.update([detection], 0, 1000)

        self.assertEqual(confirmed, [])
        self.assertEqual(completed, [])


if __name__ == "__main__":
    unittest.main()
