# Open Surveillance AI Handoff

Read this file first in the next coding session, then read `AGENTS.md` and `MILESTONES.md`.

## Current status

Milestones 0 and 1 are complete. Detection, temporary tracking, dwell confirmation, and per-incident evidence capture are implemented and covered by unit and pipeline tests. The user reports completing real-world validation; clip count and case-by-case results were not recorded.

Run the application from the repository root:

```powershell
uv run python main.py
```

For a local MP4, run `uv run python main.py --video "clip.mp4"`. This uses the same detection, tracking, incident, evidence, and display pipeline. No flag keeps DroidCam. MP4 mode needs no `DROIDCAM_INDEX`; `.env` still validates `PERSON_CONFIDENCE`.

Press `Q` to exit. A confirmed incident produces its own numbered folder under `incidents/`, containing `incident.mp4` and `incident.json`. Console reports confirmation when the two-second dwell passes, then reports the saved clip after post-roll finishes.

## Incident behavior

- The full camera frame is the restricted area.
- YOLO detects people; BoT-SORT assigns temporary IDs that reset when the process restarts.
- Confirm a track after two seconds. Preserve pending dwell through 30 missed frames; remove it after the next missed frame.
- Keep ten seconds of footage before first detection. Continue each confirmed incident through ten seconds after final track removal.
- A same-ID return during post-roll continues the current clip and restarts the timer after its next exit.
- MP4 uses 30 FPS: repeat the previous image across capture gaps and drop captures above 30 FPS. Evidence excludes display overlays.
- JSON records zone, track, entry, confirmation, clip path, and completion. Completed incidents include exit, removal, close, and duration; early shutdown marks an active clip incomplete.
- MP4 input processes every frame as fast as possible. Dwell and evidence use `CAP_PROP_POS_MSEC` decoder timestamps; invalid or non-increasing timestamps are rejected without an FPS fallback.
- MP4 metadata dates use run-start time plus video position, not the original recording date. EOF or `Q` releases resources and saves active evidence incomplete without inventing post-roll footage.

## Validation status

- Unit and pipeline suite: 49 tests passed, including MP4 source validation, repeated replay, and EOF/Q evidence cleanup.
- Synthetic MP4 round-trip: passed at 30 FPS with elapsed duration preserved.
- MP4 replay tests use generated footage and scripted detections; real-person MP4 inference was not tested.
- Real-world validation: user reports complete. Clip count and case-by-case results were not recorded.

Use `MILESTONES.md` as the source of truth for the current implementation slice and scope guards. Keep `DROIDCAM_INDEX` in the local `.env`; never commit it.
