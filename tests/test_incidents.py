import unittest

from surveillance.application.incidents import IncidentTracker
from surveillance.models import TrackedDetection


def person(track_id: int | None) -> TrackedDetection:
    return TrackedDetection(0, 0, 10, 10, 0.9, track_id)


class IncidentTrackerTests(unittest.TestCase):
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
