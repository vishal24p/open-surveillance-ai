# Open Surveillance AI

Student-sized video intelligence project for local-first restricted-zone monitoring.

## Problem

A camera watches an area continuously, but a person cannot monitor it all the time. The system should detect a person in the restricted area, confirm the intrusion, preserve evidence, and eventually make incidents searchable. In V1, the entire camera frame is the restricted area.

V1 rule: the entire camera frame is the restricted area. The runner detects people anywhere in that frame, BoT-SORT assigns temporary IDs, and a track seen for two seconds confirms an incident. Every confirmed incident gets its own numbered folder under `incidents/`, with `incident.mp4` and `incident.json` inside. The clip includes footage from ten seconds before first detection through ten seconds after final track removal. A same-track return during post-roll continues that incident without another dwell. Green boxes are detection overlays, not a zone boundary. Configurable zones may come in a future version.

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

The current runner receives the live stream, detects people, tracks temporary IDs, confirms dwell incidents, and saves evidence clips under `incidents/`. The user reports completing real-world incident validation. Incident understanding and search follow in later milestones; configurable zones are outside V1.

Evidence plays at 30 FPS with real elapsed timing: gaps repeat the last captured frame, and captures above 30 FPS are dropped. JPEG pre-roll reduces memory use; clips contain raw camera images without detection overlays. JSON records the track ID, full-frame zone, entry and confirmation times, clip path, and completion status; completed incidents also include exit, removal, close, and duration fields. If recording stops early, JSON marks the clip incomplete.

```text
incidents/
├── 1/
│   ├── incident.mp4
│   └── incident.json
└── 2/
    ├── incident.mp4
    └── incident.json
```

See [MILESTONES.md](MILESTONES.md) for current order, pass conditions, and the next implementation slice.

## Code structure

`main.py` wires components only. Runtime responsibilities are separated under `surveillance/`: configuration in `config.py`, shared data in `models.py`, camera input in `camera/`, YOLO/BoT-SORT in `perception/`, OpenCV display in `rendering/`, and frame orchestration, dwell tracking, and evidence writing in `application/`. Future storage and configurable-zone modules should follow the same boundary rule.

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
