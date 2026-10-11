# Evidence Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Keep confirmed incident information when evidence startup or finalization fails, and cover the practical runtime paths with repeatable checks.

**Architecture:** Keep EvidenceRecorder and LivePipeline interfaces. Save incomplete JSON when the incident folder is created, before decoding or writing footage. Retain active records until finalization succeeds; use the existing cleanup path after failures. Replace metadata atomically using a temporary file beside it so a failed update does not destroy the previous incomplete record.

**Tech Stack:** Existing Python 3.11, OpenCV, NumPy, unittest, uv, Windows, GitHub Actions. No new runtime dependencies.

**Spec:** MILESTONES.md Milestone 1, current review findings, and user instruction to skip hypothetical rare edge cases and keep the simplest working logic.

## Global Constraints

- Preserve user changes, existing module boundaries, raw footage, 30 FPS playback, two-second dwell, and ten-second post-roll.
- Skip picture-size handling and the rare exact-deadline change following the user's latest direction.
- No new recording options, classes, retry framework, CPU fallback, or automatic image resizing.
- Do not claim full coverage or real tracking accuracy from mock tests.
- Disk failure can prevent any new metadata write; keep the last successful file and surface the error.
- No commits, remote writes, or camera capture required for these code fixes.

## Review Focus

- First or later pre-roll decode failure must leave incomplete JSON.
- Final frame write or writer release failure must leave incomplete JSON and attempt cleanup.
- Failed metadata replacement must preserve previous JSON.
- Failure in one incident must not prevent release of the other writers.
- Normal completion must still produce complete JSON and playable evidence with unchanged timing.

### Task 1: Evidence lifecycle recovery

**Files:** Modify surveillance/application/evidence.py and tests/test_evidence.py; verify tests/test_live_pipeline.py callers. No signature changes.

- [ ] Add regressions for incomplete JSON immediately after startup, failed first/later decode, writer startup failure, and final write/release/metadata failure. Assert JSON and resource outcomes rather than private state alone.
- [ ] Run `uv run --no-sync python -m unittest discover -s tests -p test_evidence.py -v`; observe the new recovery assertions fail.
- [ ] Write incomplete metadata before buffering decode/writer setup, reuse existing _metadata, retain finalizing records until successful completion, and replace JSON through a sibling temporary file. Remove the unused stamp calculation while touching its startup code. Keep existing release/error handling.
- [ ] Add a failed replacement check proving existing JSON survives; add a real MP4 normal-completion round-trip check for playable frames and unchanged duration.
- [ ] Run the evidence and pipeline tests; ensure every failure case keeps an incomplete record when storage is writable.

### Task 2: Practical test gaps

**Files:** Add tests/test_droidcam.py; extend tests/test_renderer.py, tests/test_perception.py, and tests/test_live_pipeline.py only where existing tests leave meaningful behavior unchecked.

**Interfaces:** Existing DroidCamSource, OpenCVRenderer, YoloTracker, and LivePipeline. Production wrappers stay unchanged unless a check reveals a concrete bug.

- [ ] Check camera failed-open release and normal disconnect/close, renderer Q/continue/cleanup, and YoloTracker CUDA guard and track arguments using external-boundary mocks.
- [ ] Exercise source-read, drawing/display, and evidence exceptions through real LivePipeline cleanup. Avoid redundant checks of trivial forwarding.
- [ ] Run `uv run --no-sync python -m unittest discover -s tests -v` and record actual results.
- [ ] Run a blank-frame inference check with available local weights and CUDA. Explicitly label it startup verification, not person/ID accuracy validation.
- [ ] Record real-person replay and connected-phone validation as outstanding if footage/hardware is unavailable; do not invent test footage or successful results.

### Task 3: Repeatable checks and documentation

**Files:** Add .github/workflows/tests.yml; narrowly update README.md and HANDOFF.md while preserving their existing user edits.

- [ ] Add one Windows/Python 3.11 push/PR job using locked uv installation and `uv run --locked python -m unittest discover -s tests -v`. No new coverage gate or dependency split.
- [ ] Verify action versions against official documentation before writing the workflow; run its test command locally. Remote CI execution remains unverified until pushed.
- [ ] Measure local line coverage with Python's standard-library trace in temporary output if useful; never use trace as CI's required test command because it can lose unittest's failure exit status.
- [ ] Document incomplete metadata recovery and accurate test/hardware verification status, then run the full suite and inspect the focused diff.

## Execution

Reuse the existing evidence/test and camera reviewers for their established areas. Root owns evidence.py and metadata tests; the camera reviewer can own wrapper tests; the test reviewer can own CI. No overlapping source edits. Review the final diff together, keep fixes minimal, and preserve all pre-existing changes.

## Verification record

- Tasks 1–3 implemented in the existing checkout, preserving user changes; no commits or remote writes.
- Recovery regressions failed on the original evidence code and passed after the focused lifecycle/metadata changes.
- `uv run --locked python -m unittest discover -s tests -v`: 65 tests passed.
- Real MP4 round-trip: 391 decoded frames at 30 FPS for 13 seconds plus the initial frame; complete JSON preserved after close.
- Blank-frame CUDA inference and two valid supplied MPG frames passed; no people detected on those two frames. No live camera or full real-person tracking validation.
- Reviewer found no blocking evidence defect in the approved scope. Windows workflow syntax/settings validated; remote CI remains unchecked.
- Supplied MPG fails on intermediate repeated timestamps. Conversion/fallback choice pending; do not change the strict source rule silently.
