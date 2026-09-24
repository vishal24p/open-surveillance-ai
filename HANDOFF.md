# Open Surveillance AI Handoff

Read this file first in the next coding session, then read `AGENTS.md`.

## Current status

Project initialized on branch `master`. Repository had no prior files or commits.

Created:

- `AGENTS.md` — agent workflow rules.
- `README.md` — problem statement, V1 boundary, setup direction.
- `pyproject.toml` — Python 3.11 project dependencies.
- `uv.lock` — resolved dependency lockfile.
- `.gitignore` — Python, secrets, generated video/data exclusions.
- `docs/skills-and-plugins.md` — required workflow skills and plugins.

DroidCam, person-detection, and temporary tracking code is split under `surveillance/`: `camera/` owns capture, `perception/` owns YOLO/BoT-SORT, `rendering/` owns OpenCV display, `application/` owns the live loop, and `main.py` wires them. The runner detects COCO `person` objects, uses persistent BoT-SORT tracking, and draws green boxes, confidence, temporary IDs, and a people count. The entire camera frame is currently the restricted area; custom polygons or zone boxes are future work. Dependencies are installed through `uv`.

## Settled decisions

- Product: restricted-zone surveillance assistant.
- V1 incident: tracked person enters a user-defined polygon and remains at least 2 seconds. Current temporary zone: entire camera frame.
- Detection boxes are person overlays, not zone boundaries.
- Track IDs are temporary per process, not face identities; they reset when the runner restarts.
- Milestone 0: phone-camera streaming passed.
- Camera source: Android phone using DroidCam as a Windows virtual webcam.
- Connection: phone and laptop through USB; no cloud camera service.
- First interface: CLI/OpenCV live window; no web UI.
- Tooling: Python 3.11 + `uv`.

## Camera checkpoint

The DroidCam USB smoke test has passed on this machine:

```text
Android phone + DroidCam USB
        -> OpenCV Media Foundation camera
        -> live window on laptop
        -> Q exits cleanly
```

Run `uv run python main.py` before starting a new video module. Verify moving phone frames, person detection, and the `People: N` label. A camera handle opening is not sufficient.

Use `MILESTONES.md` as the source of truth for the current implementation slice and scope guards.

## Configuration note

`pyproject.toml` intentionally has no configuration dependency. Copy `.env.example` to `.env`; use `DROIDCAM_INDEX=1` unless Windows assigns DroidCam another index.

## Verification already completed

- `py -3.11` validated `pyproject.toml` as TOML.
- `uv lock` resolved the project dependencies.
- `uv lock --check` passed.
- `git diff --check` passed.

The `python` command is not on PATH; use `py -3.11` or `uv run` on this machine.

## Workflow for next session

1. Read `HANDOFF.md` and `AGENTS.md`.
2. Follow the required skills in `docs/skills-and-plugins.md`.
3. Run the DroidCam smoke test before a video-related implementation.
4. Add one minimal runnable check for non-trivial logic.
5. Verify fresh command output before claiming completion.

## Do not assume

- The Windows camera index assigned to DroidCam.
- USB/DroidCam connectivity.
- GPU/CUDA availability.
- That the stream works before a manual DroidCam preflight.
- That later dwell, polygon-zone, VLM, or search requirements are finalized.
