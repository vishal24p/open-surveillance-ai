# Open Surveillance AI

Version 1.0.0: local-first full-frame person incident detection and evidence recording.

## Problem

A camera watches an area continuously, but a person cannot monitor it all the time. The system should detect a person in the restricted area, confirm the intrusion, preserve evidence, and eventually make incidents searchable. In V1, the entire camera frame is the restricted area.

V1 rule: the entire camera frame is the restricted area and incident anchor. Any people present for two uninterrupted seconds confirm one frame incident. Individual entrances, departures, or tracking-ID changes do not split it while anyone remains. An empty frame before confirmation resets the timer. After confirmation, ten seconds with nobody detected end the incident; anyone returning before that deadline continues the same incident. Every incident gets its own numbered folder under `incidents/`, with `incident.mp4` and `incident.json` inside. The clip includes ten seconds before first detection through the ten-second empty interval. Green boxes and temporary BoT-SORT IDs label detections; they do not control incidents. Configurable zones may come in a future version.

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

The current runner receives the live stream, detects people, tracks temporary IDs, confirms dwell incidents, and saves evidence clips under `incidents/`. V1 freezes this frame-based architecture. Real-person validation of this architecture is pending. V1 uses no VLM; incident understanding, search, and configurable zones remain future work.

Evidence plays at 30 FPS with real elapsed timing: gaps repeat the last captured frame, and captures above 30 FPS are dropped. JPEG pre-roll reduces memory use; clips contain raw camera images without detection overlays. JSON records the full-frame zone, entry and confirmation times, clip path, and completion status; completed incidents also include exit, close, and duration fields. Exit means the first empty frame in the final empty interval. If recording stops while people remain or before ten empty seconds pass, JSON marks the clip incomplete. Previously saved incidents are left untouched.

Incomplete JSON is saved before video writing starts. Successful completion replaces it with complete metadata. Startup or finalization failures preserve the incomplete record; failed metadata updates preserve the previous JSON. Storage errors are reported and can prevent new files from being saved.

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

Requirements: Windows, Python 3.11, `uv`, and an NVIDIA GPU with a driver compatible with the locked CUDA 13.0 PyTorch build. The current tracker requires CUDA; CPU-only execution is unsupported. Run from the repository root. Ultralytics loads `yolo26s.pt` there and downloads the weights on first use if absent, requiring internet access; weights are not included in the release source archive.

```powershell
uv sync --locked
```

Install DroidCam on the phone and its Windows client. Connect the phone by USB, enable DroidCam's USB connection, then run:

```powershell
Copy-Item .env.example .env
uv run python main.py
```

The camera window opens on success. Press `Q` to close it. Change `DROIDCAM_INDEX` in `.env` if Windows assigns DroidCam another index.

To evaluate a local MP4 through the same detection, tracking, incident, evidence, and display pipeline:

```powershell
uv run python main.py --video "clip.mp4"
```

Without `--video`, the runner uses DroidCam. MP4 mode needs no `DROIDCAM_INDEX`; `.env` still supplies the validated `PERSON_CONFIDENCE` setting. It processes every frame as fast as possible, using OpenCV's `CAP_PROP_POS_MSEC` decoder timestamps for dwell and evidence timing. Invalid or non-increasing timestamps are rejected, except for one invalid final frame after valid footage when the next decoder read reaches EOF. That frame is discarded with a console message and timing stays at the last valid position; there is no FPS fallback.

MP4 metadata dates use the run-start time plus video position, not the original recording date. EOF or `Q` releases resources and saves active evidence with incomplete metadata; it does not invent post-roll footage.

## Known V1 limitations

- Real-person validation is pending. Automated tests use scripted detections and synthetic footage; they do not measure missed people, false alarms, or tracking accuracy.
- Every part of the frame is restricted. Camera movement, occlusion, and detector misses can affect occupancy; tracking IDs do not provide an incident grace period.
- Videos need finite, non-negative, strictly increasing decoder timestamps. The supplied `Meet_Crowd.mpg` has repeated intermediate timestamps and is rejected. Convert such footage to an MP4 with valid timestamps before evaluation; V1 has no timestamp fallback or built-in conversion. Only one invalid final frame after valid footage may be discarded when the next decoder read reaches EOF.
- EOF or early shutdown can leave incomplete evidence. Clips depend on available captured footage and writable storage; MP4 dates refer to evaluation time, not the source recording date.

## Design direction

Run automated checks with `uv run --locked python -m unittest discover -s tests -v`. GitHub Actions runs the same checks on Windows for pushes and pull requests. These tests cover recording failures and camera/display wrappers; they do not establish real-world detection accuracy.

Use coarse-to-fine video intelligence: cheap local perception first, selective deeper analysis only for confirmed incidents, and evidence-backed answers with timestamps.
