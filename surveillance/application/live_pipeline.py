from contextlib import ExitStack
from time import monotonic, time


class LivePipeline:
    def __init__(self, source, tracker, renderer, incidents, evidence, clock=None) -> None:
        self._source = source
        self._tracker = tracker
        self._renderer = renderer
        self._incidents = incidents
        self._evidence = evidence
        self._clock = clock

    def run(self) -> None:
        print("Video source opened. Press Q to stop.")
        try:
            while True:
                ok, frame = self._source.read()
                if not ok:
                    print("Video source ended or disconnected.")
                    break

                raw_frame = frame.copy()
                if self._clock is None:
                    now, epoch = monotonic(), time()
                else:
                    now, epoch = self._clock()
                detections = self._tracker.track(frame)
                confirmed, completed = self._incidents.update(
                    detections,
                    now,
                    epoch,
                )
                pending = self._incidents.pending_started_at
                history_start = min(
                    [incident.started_at for incident in confirmed]
                    + ([pending] if pending is not None else []),
                    default=None,
                )
                self._evidence.buffer_frame(raw_frame, now, history_start)
                self._evidence.write_active_frame(raw_frame, now, completed)
                for incident in completed:
                    self._evidence.finish_incident(incident)
                    print(
                        "Incident clip saved: "
                        f"track #{incident.incident.track_id}"
                    )
                for incident in confirmed:
                    path = self._evidence.start_incident(incident)
                    print(
                        f"Incident confirmed for track #{incident.track_id}; "
                        f"saving {path}"
                    )

                self._renderer.draw(frame, detections)
                if not self._renderer.show(frame):
                    break
        finally:
            with ExitStack() as cleanup:
                cleanup.callback(self._evidence.close)
                cleanup.callback(self._renderer.close)
                cleanup.callback(self._source.close)
