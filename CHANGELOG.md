# Changelog

## [1.0.0] - 2026-10-11

### Frozen V1 scope

- Local DroidCam USB input and local video evaluation through `--video`.
- The full frame is the restricted area. Any people detected for two uninterrupted seconds confirm one incident, including detections without tracking IDs.
- Individual arrivals, departures, and ID changes do not split an occupied scene. Ten empty seconds close the incident; anyone returning before that deadline continues it, while a return at or after the deadline starts a new dwell.
- Each incident saves raw `incident.mp4` and `incident.json` in its own numbered folder, preserving existing evidence. Available pre-roll covers ten seconds before entry; evidence continues through the final ten-second empty interval.
- Evidence plays at 30 FPS with elapsed timing. Startup, storage, finalization, and shutdown failures preserve incomplete metadata where possible and release resources.
- Added 27 regressions for the frame-based architecture, bringing the suite to 96 passing tests. No VLM is included; incident understanding, search, and configurable zones remain future work.

### Known limitations

- Real-person validation of the current architecture is pending; automated tests do not establish detector accuracy.
- CUDA is required. Model weights are downloaded on first use if absent and are not bundled in source archives.
- Invalid first-frame and intermediate video timestamps are rejected, including repeated timestamps in the supplied `Meet_Crowd.mpg`. V1 retains the existing exception for a single invalid final frame after valid footage when the next read reaches EOF; no FPS fallback or built-in conversion is provided.
- EOF or early shutdown marks active evidence incomplete. MP4 calendar timestamps use run-start time plus video position, not the original recording date.

## [0.2.0] - 2026-10-11

### Added

- Confirm a full-frame restricted-area incident after any people remain detected for two uninterrupted seconds. Tracking IDs are display labels only.
- Save each confirmed incident in its own numbered folder with an MP4 clip and JSON metadata, preserving existing evidence across runs.
- Retain ten seconds before first detection and ten seconds after the first empty frame in the final empty interval. Any person returning before the empty deadline continues the incident.
- Evaluate local MP4 footage with `--video`, using video timestamps through the same detection, tracking, incident, and evidence pipeline.

### Changed

- Evidence uses raw frames at 30 FPS with elapsed playback timing: capture gaps repeat the previous frame and captures above 30 FPS are dropped.
- Shutdown, video EOF, and runtime errors release resources; active recordings are preserved with incomplete metadata when post-roll cannot finish.
- Camera and MP4 modes share a source-neutral display and console messages.
