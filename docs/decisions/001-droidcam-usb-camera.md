# ADR-001: Use DroidCam USB through Media Foundation

## Status

Accepted

## Date

2026-09-19

## Context

The first project checkpoint needs a low-latency Android camera feed in OpenCV on Windows. DroidCam Client can preview phone video, but that preview alone does not prove its `DroidCam Video` virtual camera can deliver frames to OpenCV.

DirectShow (`cv2.CAP_DSHOW`) opened the laptop webcam at index `0` but could not capture DroidCam at index `1`. Media Foundation (`cv2.CAP_MSMF`) is the working OpenCV backend for the DroidCam numeric index on this machine. A failed virtual-driver stream can look like a green or blank OpenCV window even when DroidCam Client preview works.

## Decision

Use DroidCam over USB, configured by `DROIDCAM_INDEX` in local `.env`, and open it through `cv2.CAP_MSMF`.

The acceptance check is `uv run python camera_test.py` with changing phone frames. `VideoCapture.isOpened()` alone is not sufficient.

## Alternatives considered

### DirectShow numeric index

Rejected. It could not capture the DroidCam virtual camera by index on this machine.

### RTSP or Wi-Fi camera streaming

Rejected for this checkpoint. USB DroidCam is smaller, local, and avoids network-latency setup.

### Laptop webcam

Rejected as the project camera source. It is only useful to prove OpenCV itself can capture video.

## Consequences

- `.env` must select the correct Windows camera index per machine.
- A green or blank window is a stream failure to troubleshoot at DroidCam/Windows-driver level before changing application code.
- Future video modules may assume only that `camera_test.py` has passed; they must not assume a fixed index or DirectShow support.
