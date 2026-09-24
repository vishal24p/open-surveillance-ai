import cv2


class DroidCamSource:
    def __init__(self, index: int) -> None:
        self._camera = cv2.VideoCapture(index, cv2.CAP_MSMF)
        if not self._camera.isOpened():
            self._camera.release()
            raise RuntimeError(
                f"DroidCam was not found at camera index {index}. "
                "Set DROIDCAM_INDEX to the correct Windows camera index."
            )

    def read(self):
        return self._camera.read()

    def close(self) -> None:
        self._camera.release()
