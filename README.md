# Open Surveillance AI

Student-sized video intelligence project for local-first restricted-zone monitoring.

## Problem

A camera watches an area continuously, but a person cannot monitor it all the time. The system should detect a person entering a restricted zone, confirm the intrusion, preserve evidence, and eventually make incidents searchable.

Current behavior: the entire camera frame is treated as the restricted area. The detector finds people anywhere in that frame, and BoT-SORT assigns temporary IDs across frames. Green boxes are detection overlays, not the restricted-zone boundary. User-drawn polygons or zone boxes come in a future version.

## V1 boundary

```text
Android phone camera + DroidCam
        |
        | USB virtual webcam
        v
OpenCV on laptop
        |
        v
Restricted-zone incident pipeline
```

The current runner receives the live stream, detects people, and tracks temporary IDs. Later stages will be added one at a time: dwell/incident logic, configurable zone logic, evidence capture, incident understanding, and search.

See [MILESTONES.md](MILESTONES.md) for current order, pass conditions, and the next implementation slice.

## Code structure

`main.py` wires components only. Runtime responsibilities are separated under `surveillance/`: configuration in `config.py`, shared data in `models.py`, camera input in `camera/`, YOLO/BoT-SORT in `perception/`, OpenCV display in `rendering/`, and frame orchestration in `application/`. Future zone, dwell, incident, evidence, and storage modules should follow the same boundary rule.

## Setup

Requirements: Windows, Python 3.11, and `uv`.

```powershell
uv sync
```

Install DroidCam on the phone and its Windows client. Connect the phone by USB, enable DroidCam's USB connection, then run:

```powershell
Copy-Item .env.example .env
uv run python main.py
```

The camera window opens on success. Press `Q` to close it. Change `DROIDCAM_INDEX` in `.env` if Windows assigns DroidCam another index.

## Design direction

Use coarse-to-fine video intelligence: cheap local perception first, selective deeper analysis only for confirmed incidents, and evidence-backed answers with timestamps.
