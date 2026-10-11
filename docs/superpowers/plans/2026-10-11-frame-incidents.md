# Frame Incidents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** One incident for the entire camera view, regardless of which people enter, leave, or change tracking IDs.

**Architecture:** Replace the per-person incident dictionary with a single frame occupancy state. Replace EvidenceRecorder's per-person writer dictionary with one active writer. Keep existing perception/rendering IDs for labels only, and preserve video buffering, media clocks, raw footage, metadata recovery, and resource cleanup.

**Tech Stack:** Existing Python 3.11, OpenCV, NumPy, unittest, uv. No new dependencies or config.

**Spec:** User's frame-centered incident rule and explicit timing choices on 2026-10-11; MILESTONES.md will be updated before implementation.

## Global Constraints

- Any person detection anywhere in the full frame means occupied; missing tracking IDs do not block occupancy.
- Confirm after two uninterrupted occupied seconds. An empty frame before confirmation resets the pending timer.
- After confirmation, start the ten-second empty timer on the first frame with no people. Return before expiry continues the same incident and clears the empty timer.
- After ten empty seconds, finish that incident. An occupied frame arriving at or after the deadline starts a new two-second confirmation period.
- Any remaining person keeps the scene occupied; individual exits, entrances, and ID changes never split an incident.
- Remove obsolete per-track grace, incident track_id, track_removed_at, and multiple-writer paths rather than maintaining two modes.
- JSON retains zone: full_frame, entry/confirmation times, clip path, completion, and completed exit/close/duration fields. Exit time means the first empty frame in the final empty interval. Old saved JSON/videos stay untouched.
- The whole camera view is the incident anchor. No center-point detection gate, fabricated person ID, geographical camera configuration, or new action-understanding feature.
- Keep ten-second pre-roll, 30 FPS elapsed playback, raw images, incomplete metadata recovery, EOF/Q cleanup, and existing source timestamp rules.

## Review Focus

- Two people remain while a third enters/leaves: exactly one incident/clip.
- Person/ID handoff without an empty frame: confirmation timer continues.
- Brief vacancy after confirmation: return continues the same incident.
- Full vacancy before confirmation: short appearance cannot confirm later.
- Full vacancy after confirmation followed by expiry/re-entry: correct close time and a separate new incident, with safe evidence cleanup.

### Task 1: Frame occupancy lifecycle

**Files:** Modify surveillance/application/incidents.py, tests/test_incidents.py, and MILESTONES.md.
**Interfaces:** Keep IncidentTracker.update(detections, now, epoch) returning confirmed/completed lists, and pending_started_at. Remove ConfirmedIncident.track_id and CompletedIncident.removed_at/removed_epoch. Entry, confirmation, exit, closed, and duration remain.

- [ ] Update MILESTONES.md to the approved frame-level rule.
- [ ] Replace per-person tests with frame occupancy tests: multiple people, partial departure, ID handoff, untracked person, pending reset, two-second confirmation, return before ten empty seconds, expiry and sequential incident.
- [ ] Run the incident tests and observe the old implementation fail these requirements.
- [ ] Replace per-person state/removal loops with one optional scene state and an empty timer. Remove TRACK_LOST_FRAMES; do not change BoT-SORT configuration.
- [ ] Run incident tests and confirm the frame-level contract.

### Task 2: One evidence writer and frame-based messages

**Files:** Modify surveillance/application/evidence.py, surveillance/application/live_pipeline.py, tests/test_evidence.py, and tests/test_live_pipeline.py.
**Interfaces:** EvidenceRecorder's public start/write/finish/close signatures remain; updated incident dataclasses come from Task 1.

- [ ] Adapt evidence fixtures to frame incident records. Replace multi-writer tests with single-writer cleanup and sequential incidents; retain all prior startup/finalization/atomic JSON regression tests.
- [ ] Add a pipeline regression covering a 30-second three-person scene with the third arriving/leaving while two remain. Assert one folder/video/JSON and incomplete EOF status; add completed/sequential frame incidents.
- [ ] Observe failing integration tests before adapting EvidenceRecorder and messages.
- [ ] Replace writer dictionary with one optional record; write active frames up to the scene deadline, finalize and clear only after successful metadata save, and reject accidental second starts without abandoning the active writer.
- [ ] Remove person-ID and track-removal fields/messages. Preserve metadata recovery and release/error handling.
- [ ] Run evidence and pipeline checks, including real MP4 round-trip and replay timing.

### Task 3: Documentation and verification

**Files:** Update README.md and HANDOFF.md; maintain this plan's verification record. No new production files.

- [ ] Document one incident per occupied camera view, the two-second confirmation, ten empty seconds, EOF incomplete behavior, and scene metadata meaning.
- [ ] Run `uv run --locked python -m unittest discover -s tests -v` and `git diff --check`.
- [ ] Reuse existing reviewers to check that no incident/evidence caller still depends on a person's ID and no old mode remains.
- [ ] Report test evidence and limits honestly. Do not change the MPG timestamp policy, resize handling, or existing saved incidents.

## Execution ownership

Reuse incident_logic for incidents.py/test_incidents.py after approval; root owns evidence.py/test_evidence.py; camera_pipeline can own live_pipeline.py/test_live_pipeline.py. Each worker preserves others' edits. Root updates docs and runs the full suite. No commits or remote writes.

## Verification record

- Approved timing and execution; Tasks 1–3 implemented in the existing checkout, preserving pre-existing changes and saved incidents.
- Incident tests: old per-person implementation failed eight assertions; nine frame lifecycle tests now pass.
- Pipeline regression: old code made three folders for the 30-second example; new code makes one, with 901 decoded MP4 frames at 30 FPS. Still occupied at EOF means incomplete metadata.
- Evidence now uses one writer; startup/finalization/atomic metadata recovery, accidental second-start rejection, and sequential clips pass.
- `uv run --locked python -m unittest discover -s tests -v`: 69 tests passed.
- `git diff --check`: clean. Peer review found no blocking issue in the new scene/evidence paths.
- No new dependencies, per-person fallback mode, camera positioning configuration, or stored-file migration.
- New real-person/live-camera grouping and remote CI remain unverified. MPG intermediate timestamp handling is unchanged and still requires a separate decision.
