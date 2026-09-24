# Milestones

## Project goal

Detect a person entering a user-defined restricted zone, confirm at least two seconds of presence, save evidence, then make confirmed incidents understandable and searchable.

## Milestone 0 — Live phone camera ✅

Android phone → DroidCam USB → Windows → OpenCV live window.

Pass: the current camera runner shows changing phone video and `Q` closes it.

Notes: use `DROIDCAM_INDEX` from local `.env` and `cv2.CAP_MSMF`. See [DroidCam runbook](docs/runbooks/droidcam.md).

## Milestone 1 — Reliable restricted-zone incidents

Goal: create an incident only when a tracked person remains inside a configured polygon for at least two seconds. Until polygon configuration exists, the entire camera frame is the temporary restricted area.

Build in this order:

1. **Current:** person detection runs on live DroidCam video. It draws green person boxes, confidence, and a top-right people count. These boxes show detections; they are not the restricted-zone boundary.
2. **Current:** use persistent BoT-SORT tracking so each person keeps a temporary track ID across frames; accuracy-first configuration allows roughly one second of missed detections.
3. **Future:** define one restricted polygon and use bounding-box bottom-center as person position. Until then, use the full frame as the restricted area.
4. Start/stop a per-track dwell timer; emit one incident after two seconds inside.
5. Save evidence: ten seconds before, full incident, and ten seconds after.
6. Test with 10–20 clips: true entry, near miss, brief crossing, multiple people, partial occlusion, and exit.

Pass: incident output includes zone, track ID, entry/confirmation/exit times, duration, and evidence-clip path. No VLM decides whether an intrusion occurred.

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
