class LivePipeline:
    def __init__(self, source, tracker, renderer) -> None:
        self._source = source
        self._tracker = tracker
        self._renderer = renderer

    def run(self) -> None:
        print("DroidCam connected. Press Q to stop.")
        try:
            while True:
                ok, frame = self._source.read()
                if not ok:
                    print("Lost DroidCam video.")
                    break

                detections = self._tracker.track(frame)
                self._renderer.draw(frame, detections)
                if not self._renderer.show(frame):
                    break
        finally:
            self._source.close()
            self._renderer.close()
