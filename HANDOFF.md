# Open Surveillance AI Handoff

Read this file first in the next coding session, then read `AGENTS.md` and `MILESTONES.md`.

## Current status

Version 1.0.0 freezes Milestones 0 and 1, including local MP4 evaluation. Detection, temporary display tracking, frame occupancy confirmation, and evidence capture are covered by unit and pipeline tests. The frame-based architecture is current; real-person validation remains pending, as confirmed by the user for this release. VLM analysis, search, and configurable zones are future scope.

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

- V1 release verification: 96 tests passed locally with `uv run --locked python -m unittest discover -s tests -v`. Added 27 regressions across incident timing, repeated visits/returns, evidence recovery/resampling, cleanup boundaries, media timestamps, and CLI fail-fast behavior. These include frame occupancy/ID handoff, partial departures, empty deadline/return, sequential scene incidents, metadata recovery, camera/display/YOLO wrappers, MP4 replay, EOF/Q cleanup, and final-frame timestamp checks.
- Release startup smoke: CUDA was available and two blank-frame tracking calls returned zero detections with the local model. This checks startup only; real-person accuracy remains pending.
- The scripted 30-second three-person regression produces one folder/video/JSON: two remain while a third enters/leaves. Its MP4 decodes 901 frames at 30 FPS and EOF marks the still-occupied incident incomplete.
- Synthetic MP4 round-trip: passed at 30 FPS with elapsed duration preserved.
- MP4 replay tests use generated footage and scripted detections. Two blank-frame CUDA calls and inference on the first two valid frames of the supplied MPG passed with the local model; both MPG frames returned no people. This verifies startup, not real-person tracking accuracy.
- The user's MPG reproduced a final-frame timestamp reset from 15.28 seconds to zero. Source-only verification now delivers 382 valid frames, discards that invalid final frame, reaches EOF at the last valid position, and releases capture. The full detection/display run was not rerun after this fix.
- Real-person validation of the current architecture: pending. Earlier user validation reports concern the preceding flow; no current accuracy measurements are claimed.
- The supplied Meet_Crowd.mpg has repeated intermediate decoder timestamps, including near its start. V1 deliberately rejects it under the strictly increasing timestamp rule; the final-frame exception does not cover this file. The user approved keeping this rule and documenting external conversion to valid-timestamp MP4 as the preparation step.
- Windows GitHub Actions passed on the pre-release commit b7648dc8aca80ec4b16cd060b78eeef724dc43c7. Recheck CI for the final release commit before publication.
- Picture-size handling remains excluded. The new approved frame rule explicitly closes at ten empty seconds, including when someone arrives at that deadline; the old per-person deadline logic is removed.

Use `MILESTONES.md` as the source of truth for the current implementation slice and scope guards. Keep `DROIDCAM_INDEX` in the local `.env`; never commit it.
