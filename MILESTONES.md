# Milestones

## Project goal

Detect a person in the restricted area, confirm at least two seconds of presence, save evidence, then make confirmed incidents understandable and searchable. In V1, the entire camera frame is the restricted area.

## Milestone 0 — Live phone camera ✅

Android phone → DroidCam USB → Windows → OpenCV live window.

Pass: the current camera runner shows changing phone video and `Q` closes it.

Notes: use `DROIDCAM_INDEX` from local `.env` and `cv2.CAP_MSMF`. See [DroidCam runbook](docs/runbooks/droidcam.md).

## Milestone 1 — Reliable restricted-zone incidents ✅

Goal: create an incident only when a tracked person remains in the camera frame for at least two seconds. The entire frame is the V1 restricted area; configurable polygons are future work.

Build in this order:

1. **Current:** person detection runs on live DroidCam video. It draws green person boxes, confidence, and a top-right people count. These boxes show detections; they are not the restricted-zone boundary.
2. **Current:** use persistent BoT-SORT tracking so each person keeps a temporary track ID across frames; accuracy-first configuration allows roughly one second of missed detections.
3. **Implemented:** start dwell on first detection and confirm one incident for that track after two seconds in the full frame.
4. **Implemented:** save each confirmed incident to its own numbered folder under `incidents/`, containing `incident.mp4` and `incident.json`. The clip covers ten seconds before first detection through ten seconds after final track removal. A same-track return during post-roll continues the incident without another dwell and restarts post-roll after its next exit. MP4 uses 30 FPS with elapsed-time playback: repeat the previous frame across capture gaps and drop captures above 30 FPS. Clips contain raw frames without display overlays; early shutdown marks JSON incomplete.
5. **Validation complete:** the user reports testing the incident flow. Clip count and case-by-case results were not recorded in the repository.

Pass: incident output includes the full-frame zone, track ID, entry/confirmation/exit times, duration, and evidence-clip path. No VLM decides whether an intrusion occurred.

The dwell and evidence logic has unit and pipeline coverage. The user reports the real-world validation is complete.

### Evaluation extension — Local MP4 input

Run local MP4 files through the same detection, tracking, incident, and evidence pipeline using `uv run python main.py --video "clip.mp4"`. No flag keeps DroidCam. Use video timestamps and process frames as fast as possible so dwell and evidence timing do not depend on processing speed. At end of file, preserve available evidence and mark unfinished incidents incomplete; do not invent post-roll footage.

Pass: repeated footage has the same video-time incident timeline, MP4 mode does not require a camera index, and EOF releases capture, display, and evidence resources. MP4 calendar timestamps use run-start time plus video position; they do not represent the original recording date.

## Milestone 2 — Incident understanding

Goal: explain confirmed evidence clips without using a VLM as the security trigger.

Use selected keyframes from each incident. Produce structured output: summary, people count, ordered actions, object interactions, before/after context, and uncertainty. Escalate to stronger analysis only when local analysis is uncertain.

## Milestone 3 — Searchable incident memory

Goal: find incidents by time, zone, action, object, and summary.

Store incident metadata, evidence references, structured understanding, and retrieval indexes. Search returns timestamps and evidence before a generated answer.

## Milestone 4 — Investigation assistant

Goal: answer questions such as “What happened in the restricted area today?” with incident records and linked evidence.

The assistant retrieves first, inspects selected evidence when needed, and states uncertainty instead of inventing events.

## Scope guards

- Do not add face recognition, general anomaly detection, cloud infrastructure, a web UI, or continuous VLM analysis during Milestone 1.
- Live camera transport is already complete in Milestone 0. Earlier planning listed it later; this file is the current order.
- Before each new implementation slice, update this file if its pass condition or scope changes.
