# Open Surveillance AI

## Mission

Build a student-sized, local-first surveillance assistant inspired by NVIDIA's video-search architecture.

V1 detects a person entering a user-defined restricted polygon, confirms at least 2 seconds of presence, saves evidence, and later supports incident understanding/search.

## Current milestone

Project initialization only. Next implementation milestone is a disposable DroidCam smoke test:

`Android phone + DroidCam USB -> OpenCV on laptop -> live window`

Do not add detection, tracking, VLMs, databases, cloud APIs, or a web UI until that stream works.

## Technical constraints

- Python 3.11 with `uv`.
- Keep the first slice CLI/OpenCV-based.
- Phone and laptop communicate through DroidCam over USB.
- Prefer the smallest working dependency set and reuse existing project patterns.
- Do not build NVIDIA's production infrastructure; preserve concepts, not services.

## Working rules

- Read the relevant flow before editing it.
- Ask for a design decision when scope changes.
- Add one runnable check for non-trivial logic.
- Verify commands and outputs before claiming completion.
- Keep unrelated files and user changes untouched.

## Planned commands

```powershell
uv sync
uv run python camera_test.py
```

Copy `.env.example` to `.env` before running the camera command. Set `DROIDCAM_INDEX=1` for the usual DroidCam device index.
