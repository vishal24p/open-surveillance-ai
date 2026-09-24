from surveillance.application.live_pipeline import LivePipeline
from surveillance.camera.droidcam import DroidCamSource
from surveillance.config import load_settings
from surveillance.perception.yolo_tracker import YoloTracker
from surveillance.rendering.opencv import OpenCVRenderer


if __name__ == "__main__":
    settings = load_settings()
    pipeline = LivePipeline(
        DroidCamSource(settings.droidcam_index),
        YoloTracker(settings.person_confidence),
        OpenCVRenderer(),
    )
    pipeline.run()
