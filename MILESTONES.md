# Milestones

## Project goal

Detect a person in the restricted area, confirm at least two seconds of presence, save evidence, then make confirmed incidents understandable and searchable. In V1, the entire camera frame is the restricted area.

## V1 freeze — 1.0.0

Milestones 0 and 1, including local MP4 evaluation, define the frozen release scope. The frame-based architecture is current: any-person occupancy controls incidents; temporary person IDs only label detections. V1 contains no VLM. Milestones 2–4 and configurable zones are future work, not release requirements. Real-person validation remains pending and is documented as a release limitation.

Keep strict decoder timestamps in V1. The supplied `Meet_Crowd.mpg` repeats intermediate timestamps and is rejected; conversion to valid-timestamp MP4 footage is an external preparation step. Do not silently add an FPS fallback or broaden the final-frame exception.

## Milestone 0 — Live phone camera ✅

Android phone → DroidCam USB → Windows → OpenCV live window.

Pass: the current camera runner shows changing phone video and `Q` closes it.

Notes: use `DROIDCAM_INDEX` from local `.env` and `cv2.CAP_MSMF`. See [DroidCam runbook](docs/runbooks/droidcam.md).

## Milestone 1 — Reliable restricted-zone incidents ✅

Goal: create one incident when the camera frame remains occupied by any people for at least two uninterrupted seconds. The entire frame is the V1 restricted area and incident anchor; configurable polygons are future work.

Build in this order:

1. **Current:** person detection runs on live DroidCam video. It draws green person boxes, confidence, and a top-right people count. These boxes show detections; they are not the restricted-zone boundary.
2. **Current:** use persistent BoT-SORT tracking so each person keeps a temporary track ID across frames; accuracy-first configuration allows roughly one second of missed detections.
3. **Implemented:** start frame dwell on any person detection, including detections without tracking IDs. Confirm one incident after two uninterrupted occupied seconds; an empty frame before confirmation resets dwell. Individual entrances, exits, and tracking-ID changes do not split an occupied scene.
4. **Implemented:** save each frame incident to its own numbered folder under `incidents/`, containing `incident.mp4` and `incident.json`. The clip covers ten seconds before first detection through ten seconds after the first empty frame in the final empty interval. Anyone returning before ten empty seconds continues the same incident and clears the empty timer. Once ten empty seconds expire, finish that incident; later occupancy requires a new two-second confirmation. Per-person incident removal rules are removed; one evidence writer serves the frame. MP4 uses 30 FPS with elapsed-time playback: repeat the previous frame across capture gaps and drop captures above 30 FPS. Clips contain raw frames without display overlays; early shutdown marks JSON incomplete.
5. **Validation:** frame-level unit and pipeline checks pass, including one 30-second clip with two continuous occupants and a third entering/leaving. The user previously reported testing the earlier incident flow; the new grouping has not yet been validated with real-person footage.

Pass: two people remaining while a third enters/exits produce one frame incident and one clip. Output includes the full-frame zone, entry/confirmation/exit times, duration, and evidence-clip path; person IDs belong only to detection overlays. Exit time is the first empty frame in the final empty interval. No VLM decides whether an intrusion occurred.

The frame dwell and evidence logic has unit and pipeline coverage. Real-world validation of the new grouping remains outstanding.

### Evaluation extension — Local MP4 input

Run local MP4 files through the same detection, tracking, incident, and evidence pipeline using `uv run python main.py --video "clip.mp4"`. No flag keeps DroidCam. Use video timestamps and process frames as fast as possible so dwell and evidence timing do not depend on processing speed. At end of file, preserve available evidence and mark unfinished incidents incomplete; do not invent post-roll footage.

Pass: repeated footage has the same video-time incident timeline, MP4 mode does not require a camera index, and EOF releases capture, display, and evidence resources. MP4 calendar timestamps use run-start time plus video position; they do not represent the original recording date.

Final-frame timestamp exception: after at least one valid frame, discard one frame with an invalid timestamp only if the next decoder read reaches EOF. Keep the last valid video position and normal EOF cleanup; active evidence stays incomplete. Invalid first-frame or intermediate timestamps remain errors, with no FPS fallback.

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
