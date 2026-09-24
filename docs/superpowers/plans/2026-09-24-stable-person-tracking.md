# Stable Person Tracking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep temporary person IDs stable across consecutive frames in the fixed DroidCam view.

**Architecture:** Reuse Ultralytics tracking with `persist=True` instead of writing a custom tracker. Use an explicit BoT-SORT configuration tuned for a fixed camera, accuracy first, and roughly one second of lost-track buffering. The current full frame remains the zone; dwell and incidents stay out of scope.

**Tech Stack:** Python 3.11, OpenCV, Ultralytics YOLO26s, BoT-SORT, PyTorch CUDA.

**Spec:** User-confirmed design in this task: fixed camera, accuracy first, one-second occlusion tolerance, tracking-only first slice.

## Global Constraints

- Keep the existing CLI/OpenCV runner.
- Track only COCO `person` class.
- IDs are temporary per process; never claim they are face identities.
- Do not add polygon zones, dwell timers, incidents, recording, or storage.
- Never fabricate an ID when the tracker has not returned one.

## Review Focus

- Consecutive frames preserve the same tracker ID.
- Missing tracker IDs remain `None` and do not crash rendering.
- Multiple people display distinct IDs.
- Tracker state persists within one camera stream and resets with a new model instance.
- BoT-SORT uses static-camera motion compensation and approximately one second of track buffering.

### Task 1: Extract and display tracked detections

**Files:**
- Modify: `surveillance/camera.py`
- Modify: `tests/test_camera.py`
- Create: `surveillance/botsort_accuracy.yaml`

**Interfaces:**
- Produces: `extract_tracked_detections(result)` returning `(x1, y1, x2, y2, confidence, track_id)` tuples.
- Changes: `draw_person_detections` displays `person #ID confidence` when an ID exists.

- [x] **Step 1: Write failing tests** for ID extraction, missing IDs, and ID labels.
- [x] **Step 2: Run `uv run python -m unittest discover -s tests -v` and confirm failure.**
- [x] **Step 3: Implement extraction, rendering, and `model.track(..., persist=True)`.**
- [x] **Step 4: Add explicit static-camera BoT-SORT config with ReID enabled and `track_buffer: 30`.**
- [x] **Step 5: Run the full tests and compile check.**
- [ ] **Step 6: Manually verify live IDs with one person, two people, crossing, and brief occlusion.**
