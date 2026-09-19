from pathlib import Path


WINDOW_NAME = "DroidCam"


def get_droidcam_index(env_path: Path = Path(".env")) -> int:
    value = _read_env_value(env_path, "DROIDCAM_INDEX")

    if value is None:
        raise RuntimeError("Set DROIDCAM_INDEX in .env.")

    try:
        index = int(value)
    except ValueError as error:
        raise RuntimeError("DROIDCAM_INDEX must be a non-negative integer.") from error

    if index < 0:
        raise RuntimeError("DROIDCAM_INDEX must be a non-negative integer.")

    return index


def _read_env_value(env_path: Path, key_name: str) -> str | None:
    if not env_path.is_file():
        raise RuntimeError("Create .env from .env.example before running the camera.")

    for line in env_path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator and key.strip() == key_name:
            return value.strip().strip('"').strip("'")

    return None


def show_droidcam(index: int) -> None:
    import cv2

    camera = cv2.VideoCapture(index, cv2.CAP_MSMF)
    if not camera.isOpened():
        camera.release()
        raise RuntimeError(
            f"DroidCam was not found at camera index {index}. "
            "Set DROIDCAM_INDEX to the correct Windows camera index."
        )

    print("DroidCam connected. Press Q to stop.")
    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                print("Lost DroidCam video.")
                break

            cv2.imshow(WINDOW_NAME, frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()
