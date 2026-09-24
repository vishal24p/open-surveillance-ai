import cv2

from ..models import TrackedDetection


WINDOW_NAME = "DroidCam"


def draw_person_detections(
    frame, detections: list[TrackedDetection]
) -> None:
    for detection in detections:
        cv2.rectangle(
            frame,
            (detection.x1, detection.y1),
            (detection.x2, detection.y2),
            (0, 255, 0),
            2,
        )
        label = (
            f"person #{detection.track_id} {detection.confidence:.0%}"
            if detection.track_id is not None
            else f"person {detection.confidence:.0%}"
        )
        cv2.putText(
            frame,
            label,
            (detection.x1, max(20, detection.y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

    count_label = f"People: {len(detections)}"
    (label_width, label_height), _ = cv2.getTextSize(
        count_label, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2
    )
    cv2.putText(
        frame,
        count_label,
        (max(10, frame.shape[1] - label_width - 10), label_height + 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (0, 255, 0),
        2,
        cv2.LINE_AA,
    )


class OpenCVRenderer:
    def draw(self, frame, detections: list[TrackedDetection]) -> None:
        draw_person_detections(frame, detections)

    def show(self, frame) -> bool:
        cv2.imshow(WINDOW_NAME, frame)
        return cv2.waitKey(1) & 0xFF != ord("q")

    def close(self) -> None:
        cv2.destroyAllWindows()
