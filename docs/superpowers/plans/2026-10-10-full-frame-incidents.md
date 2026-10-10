# Full-Frame Incidents Implementation Plan

> **For agentic workers:** Execute inline in this session; keep changes small and run the listed checks.

**Goal:** Confirm a full-frame incident after two seconds of tracking, save evidence from ten seconds before first detection through ten seconds after final track removal, and merge same-track returns during post-roll.

**Architecture:** Add a small incident state manager to the application flow and a rolling raw-frame buffer/evidence writer. The incident manager owns per-track timing; the recorder writes a separate clip and metadata for each confirmed track incident.

**Tech Stack:** Python 3.11, OpenCV, unittest.

## Global Constraints

- The entire camera frame is the V1 restricted area.
- Dwell is two seconds from first detection; confirmation is recorded separately.
- Pre-roll begins ten seconds before first detection.
- A confirmed incident remains open through same-track returns during the ten-second post-exit timer; each return cancels that timer, and the next exit starts a fresh ten-second timer.
- Keep current live people count and display behavior.
- Do not add identity recognition, zone configuration, or VLM behavior.

---

### Task 1: Incident timing

**Files:**
- Create `surveillance/application/incidents.py`.
- Create `tests/test_incidents.py`.
- Modify `surveillance/application/live_pipeline.py` to feed detections and monotonic timestamps into incident tracking.

- [x] Test dwell confirmation at two seconds, short appearances that do not confirm, track loss grace, same-ID return without another dwell, timer restart after final exit, and incident close after ten absent seconds.
- [x] Implement the minimal per-track state machine and run `uv run python -m unittest discover -s tests -v`.

### Task 2: Evidence clips

**Files:**
- Create `surveillance/application/evidence.py`.
- Modify `surveillance/application/live_pipeline.py` to preserve raw frames before drawing overlays and feed the evidence writer.
- Use existing `.gitignore` rules for generated incident clips and metadata.
- Create or extend evidence tests using a fake video writer.

- [x] Verify buffered pre-roll starts ten seconds before first detection and preserves elapsed playback through final exit plus ten seconds at the approved 30 FPS.
- [x] Write one MP4 and JSON metadata per confirmed track incident, then run the full unittest suite.

### Task 3: Milestone status

**Files:**
- Update `MILESTONES.md`, `README.md`, and the DroidCam runbook to describe implemented incident behavior and leave the 10–20 real-clip validation gate open until clips are available.
- Update `HANDOFF.md` to reflect the current implementation and pending hardware/clip validation.

- [x] Confirm docs distinguish automated state-machine checks from real video validation and run `git diff --check`.

### Review fixes approved 2026-10-10

**Scope:** Preserve the existing incident requirements and repair the five ship-review findings. No new dependencies or camera configuration.

**Files and responsibilities:** `incidents.py` owns grace and exposes the earliest pending entry; `evidence.py` owns pinned JPEG history, streamed decoding, timestamp-aware writing, and reliable cleanup; `live_pipeline.py` passes pending entry times and closes every resource. Their unittest files cover each regression.

- [x] Preserve pre-confirmation dwell through BoT-SORT's 30 missing frames; check grace return, multiple tracks, and expired post-roll.
- [x] Keep ten seconds before pending entry despite delayed confirmation; release retained history when no candidate needs it.
- [x] Create the video writer before decoding the rest of the history; reject decode failures and release handles on start errors.
- [x] Release all video writers and pipeline resources despite a cleanup failure; surface the error.
- [x] Resolve fixed-FPS playback policy with the user, then check timestamps under changing cadence.
- [x] Verify full post-roll including its cutoff, raw-frame pipeline integration, shutdown, and error paths. Run `uv run python -m unittest discover -s tests -v`, `uv lock --check`, and `git diff --check`.

Hardware and 10–20 real-clip validation remain pending.

### Task 4: Incident review fixes

**Scope:** Preserve dwell across all 30 allowed missed frames, matching BoT-SORT removal after the grace expires. Expose the earliest unconfirmed entry time so evidence buffering can retain its pre-roll without changing the incident update API.

**Files:**
- Modify `surveillance/application/incidents.py`.
- Extend `tests/test_incidents.py`.

- [x] Reproduce the lost-dwell failure after 30 misses before fixing the boundary.
- [x] Test the 30/31-miss boundary, independent tracks, fresh dwell after expired post-roll, and pending entry timestamps.
- [x] Run incident tests and the full unittest suite (10 incident tests; 36 total tests passed).
