from argparse import ArgumentParser
from pathlib import Path
from time import time

from surveillance.application.live_pipeline import LivePipeline
from surveillance.application.incidents import IncidentTracker
from surveillance.application.evidence import EvidenceRecorder
from surveillance.camera.droidcam import DroidCamSource
from surveillance.camera.video_file import VideoFileSource
from surveillance.config import get_person_confidence, load_settings
from surveillance.perception.yolo_tracker import YoloTracker
from surveillance.rendering.opencv import OpenCVRenderer


def main() -> None:
    parser = ArgumentParser(description="Detect and record restricted-zone incidents.")
    parser.add_argument("--video", type=Path, help="Read a local MP4 instead of DroidCam.")
    args = parser.parse_args()
    if args.video is None:
        settings = load_settings()
        confidence = settings.person_confidence
    else:
        confidence = get_person_confidence()

    tracker = YoloTracker(confidence)
    source = DroidCamSource(settings.droidcam_index) if args.video is None else VideoFileSource(args.video)
    clock = None
    if args.video is not None:
        started_epoch = time()
        clock = lambda: (source.position_seconds, started_epoch + source.position_seconds)

    pipeline = LivePipeline(
        source,
        tracker,
        OpenCVRenderer(),
        IncidentTracker(),
        EvidenceRecorder(),
        clock=clock,
    )
    pipeline.run()


if __name__ == "__main__":
    main()
