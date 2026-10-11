# Final Video Timestamp Fix Plan

> **For agentic workers:** Use Superpowers TDD for implementation and gstack investigate for reproduction and verification. Reuse the video-source reviewer; keep it available for follow-ups.

**Goal:** Finish cleanly when a decoded video's final frame has an invalid timestamp.

**Architecture:** Keep timestamp validation in VideoFileSource.read. After at least one valid frame, probe one further capture read when a timestamp is invalid. Only a failed probe treats the invalid frame as discarded EOF; otherwise raise the existing error. Preserve the last valid position and existing pipeline EOF cleanup.

**Tech Stack:** Python 3.11, installed OpenCV, unittest; no new dependencies.

## Global Constraints

- User approved discarding one invalid final frame only when EOF follows.
- Reject invalid first-frame timestamps and invalid timestamps followed by another decoded frame.
- Do not infer timestamps from FPS or frame count; do not invent evidence or post-roll.
- Preserve existing evidence and the live camera path.

## Task 1: Source and regression tests

**Files:** surveillance/camera/video_file.py; tests/test_video_file.py.
**Interfaces:** Existing read() returns (False, None) for the accepted final-frame exception; position_seconds remains the last valid media position.

- [x] Write a regression test for valid frame, invalid final frame, then EOF. Cover zero/backward/non-finite/negative timestamps and retained position.
- [x] Verify the regression fails with the current timestamp RuntimeError.
- [x] Add the smallest EOF probe in the invalid-timestamp branch; report the discarded frame to the operator.
- [x] Keep invalid initial and intermediate timestamps rejected, including two invalid trailing frames.
- [x] Run focused source tests and reproduce with the user's actual MPG; verify 382 valid frames then EOF at 15.28 seconds and capture release.

## Task 2: Documentation and verification

**Files:** MILESTONES.md, README.md, HANDOFF.md; this plan.

- [x] Document the narrow exception and last-valid-position/incomplete-evidence semantics.
- [x] Run uv run python -m unittest discover -s tests -v, uv lock --check, and git diff --check.
- [x] Review the final diff for changed callers, timing, cleanup, and accidental broad timestamp fallback.

## Advice

Finish this bounded input fix, then check real footage for tracking stability and meaningful evidence before implementing Milestone 2 incident understanding. Decoder internals and general format conversion are outside this fix.
