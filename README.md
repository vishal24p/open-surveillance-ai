# Open Surveillance AI

Student-sized video intelligence project for local-first restricted-zone monitoring.

## Problem

A camera watches an area continuously, but a person cannot monitor it all the time. The system should detect a person entering a restricted zone, confirm the intrusion, preserve evidence, and eventually make incidents searchable.

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

The first technical checkpoint is only live-stream reception. Later stages will be added one at a time: person detection, tracking, zone logic, evidence capture, incident understanding, and search.

See [MILESTONES.md](MILESTONES.md) for current order, pass conditions, and the next implementation slice.

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
