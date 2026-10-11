# Changelog

## [0.2.0] - 2026-10-11

### Added

- Confirm a full-frame restricted-area incident after a tracked person remains for two seconds, with a grace period for missed detections.
- Save each confirmed incident in its own numbered folder with an MP4 clip and JSON metadata, preserving existing evidence across runs.
- Retain ten seconds before first detection and ten seconds after final track removal. A same-track return during post-roll continues the incident.
- Evaluate local MP4 footage with `--video`, using video timestamps through the same detection, tracking, incident, and evidence pipeline.

### Changed

- Evidence uses raw frames at 30 FPS with elapsed playback timing: capture gaps repeat the previous frame and captures above 30 FPS are dropped.
- Shutdown, video EOF, and runtime errors release resources; active recordings are preserved with incomplete metadata when post-roll cannot finish.
- Camera and MP4 modes share a source-neutral display and console messages.
