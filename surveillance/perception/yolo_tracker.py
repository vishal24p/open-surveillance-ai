from pathlib import Path

from ..models import TrackedDetection


MODEL_NAME = "yolo26s.pt"
PERSON_CLASS = 0
TRACKER_CONFIG = Path(__file__).with_name("botsort_accuracy.yaml")


def extract_tracked_detections(result) -> list[TrackedDetection]:
    boxes = result.boxes
    track_ids = boxes.id if getattr(boxes, "is_track", False) else None
    detections = []

    for index, box in enumerate(boxes):
        x1, y1, x2, y2 = (int(value) for value in box.xyxy[0].tolist())
        track_id = None if track_ids is None else int(track_ids[index])
        detections.append(
            TrackedDetection(x1, y1, x2, y2, float(box.conf[0]), track_id)
        )

    return detections


class YoloTracker:
    def __init__(self, confidence: float) -> None:
        import torch
        from ultralytics import YOLO

        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is required for the person-detection smoke test.")

        self._confidence = confidence
        self._model = YOLO(MODEL_NAME)

    def track(self, frame) -> list[TrackedDetection]:
        result = self._model.track(
            frame,
            persist=True,
            classes=[PERSON_CLASS],
            conf=self._confidence,
            device=0,
            tracker=str(TRACKER_CONFIG),
            verbose=False,
        )[0]
        return extract_tracked_detections(result)
