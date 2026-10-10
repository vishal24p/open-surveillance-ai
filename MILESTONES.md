# Milestones

## Project goal

Detect a person in the restricted area, confirm at least two seconds of presence, save evidence, then make confirmed incidents understandable and searchable. In V1, the entire camera frame is the restricted area.

## Milestone 0 — Live phone camera ✅

Android phone → DroidCam USB → Windows → OpenCV live window.

Pass: the current camera runner shows changing phone video and `Q` closes it.

Notes: use `DROIDCAM_INDEX` from local `.env` and `cv2.CAP_MSMF`. See [DroidCam runbook](docs/runbooks/droidcam.md).

## Milestone 1 — Reliable restricted-zone incidents

Goal: create an incident only when a tracked person remains in the camera frame for at least two seconds. The entire frame is the V1 restricted area; configurable polygons are future work.

Build in this order:

1. **Current:** person detection runs on live DroidCam video. It draws green person boxes, confidence, and a top-right people count. These boxes show detections; they are not the restricted-zone boundary.
2. **Current:** use persistent BoT-SORT tracking so each person keeps a temporary track ID across frames; accuracy-first configuration allows roughly one second of missed detections.
3. **Implemented:** start dwell on first detection and confirm one incident for that track after two seconds in the full frame.
4. **Implemented:** save a clip from ten seconds before first detection through ten seconds after final track removal. A same-track return during post-roll continues the incident without another dwell and restarts the post-roll after its next exit.
5. **Validation pending:** test with 10–20 clips covering sustained presence, brief appearance, multiple people, partial occlusion, and exit. The repository currently has no validation clips.

Pass: incident output includes the full-frame zone, track ID, entry/confirmation/exit times, duration, and evidence-clip path. No VLM decides whether an intrusion occurred.

The dwell and evidence logic has unit coverage; do not mark this milestone complete until the real-clip validation step passes.

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
