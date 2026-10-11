# Open Surveillance AI Handoff

Read this file first in the next coding session, then read `AGENTS.md` and `MILESTONES.md`.

## Current status

Milestones 0 and 1 are implemented. Detection, temporary display tracking, frame occupancy confirmation, and evidence capture are covered by unit and pipeline tests. The user reported real-world validation of the earlier per-person flow; the new frame grouping has not yet been checked with real-person footage.

Run the application from the repository root:

```powershell
uv run python main.py
```

For a local MP4, run `uv run python main.py --video "clip.mp4"`. This uses the same detection, tracking, incident, evidence, and display pipeline. No flag keeps DroidCam. MP4 mode needs no `DROIDCAM_INDEX`; `.env` still validates `PERSON_CONFIDENCE`.

Press `Q` to exit. One confirmed full-frame incident produces one numbered folder under `incidents/`, containing `incident.mp4` and `incident.json`. Console reports frame confirmation after two occupied seconds, then reports the saved clip after ten empty seconds.

## Incident behavior

- The full camera frame is the restricted area.
- YOLO detects people; BoT-SORT assigns temporary IDs that reset when the process restarts.
- Confirm one frame incident after two uninterrupted occupied seconds. Any person detection counts, with or without a tracking ID; an empty frame before confirmation resets dwell.
- Keep ten seconds of footage before first detection. After confirmation, start an empty timer on the first frame with nobody detected and finish after ten empty seconds.
- Anyone returning before the empty deadline continues the current incident and clears that timer. At or after the deadline, the old incident finishes and new occupancy needs two seconds to confirm.
- Multiple people, individual entrances/departures, and tracking-ID changes never split an occupied scene. The old per-person incident dictionary, 30-missed-frame incident grace, and multiple evidence writers are removed. BoT-SORT IDs remain display labels only.
- MP4 uses 30 FPS: repeat the previous image across capture gaps and drop captures above 30 FPS. Evidence excludes display overlays.
- JSON records full-frame zone, entry, confirmation, clip path, and completion. Incomplete JSON is saved before video startup; completion replaces it atomically after finalization succeeds. Startup/finalization failures retain incomplete information. Completed incidents include exit (first empty frame of the final vacancy), close, and duration. There is no person track_id or track_removed_at in new metadata; existing files are untouched. Early shutdown/EOF marks an active clip incomplete.
- MP4 input processes every frame as fast as possible. Dwell and evidence use `CAP_PROP_POS_MSEC` decoder timestamps. After valid footage, one invalid final frame is discarded with a console message only if the next decoder read reaches EOF; timing stays at the last valid position. Invalid first-frame or intermediate timestamps remain errors, without an FPS fallback.
- MP4 metadata dates use run-start time plus video position, not the original recording date. EOF or `Q` releases resources and saves active evidence incomplete without inventing post-roll footage.

## Validation status

- Unit and pipeline suite: 69 tests passed, including frame occupancy/ID handoff, partial departures, empty deadline/return, sequential scene incidents, metadata recovery, camera/display/YOLO wrappers, pipeline exception cleanup, MP4 validation/replay, EOF/Q cleanup, and final-frame timestamp checks.
- The scripted 30-second three-person regression produces one folder/video/JSON: two remain while a third enters/leaves. Its MP4 decodes 901 frames at 30 FPS and EOF marks the still-occupied incident incomplete.
- Synthetic MP4 round-trip: passed at 30 FPS with elapsed duration preserved.
- MP4 replay tests use generated footage and scripted detections. Two blank-frame CUDA calls and inference on the first two valid frames of the supplied MPG passed with the local model; both MPG frames returned no people. This verifies startup, not real-person tracking accuracy.
- The user's MPG reproduced a final-frame timestamp reset from 15.28 seconds to zero. Source-only verification now delivers 382 valid frames, discards that invalid final frame, reaches EOF at the last valid position, and releases capture. The full detection/display run was not rerun after this fix.
- Real-world validation: user reports complete. Clip count and case-by-case results were not recorded.
- The currently supplied Meet_Crowd.mpg has 492 decodable frames and repeated intermediate decoder timestamps, including near its start. It still fails the deliberate strictly increasing timestamp rule; the earlier final-frame exception does not cover this file. A conversion or timestamp-policy decision is pending.
- A Windows GitHub Actions test job was added; its locked test command is verified locally, but remote CI has not run in this session.
- Picture-size handling remains excluded. The new approved frame rule explicitly closes at ten empty seconds, including when someone arrives at that deadline; the old per-person deadline logic is removed.

Use `MILESTONES.md` as the source of truth for the current implementation slice and scope guards. Keep `DROIDCAM_INDEX` in the local `.env`; never commit it.
