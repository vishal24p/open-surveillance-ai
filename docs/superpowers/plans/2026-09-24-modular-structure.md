# Modular Surveillance Structure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the current camera module into clear component boundaries without changing runtime behavior.

**Architecture:** Keep `main.py` as the composition root. Separate configuration, domain data, camera capture, YOLO/BoT-SORT perception, OpenCV rendering, and live-loop orchestration. Use concrete components now; add ports only when a second implementation exists.

**Tech Stack:** Python 3.11, OpenCV, Ultralytics YOLO, BoT-SORT, unittest.

**Spec:** User-requested modular structure for future upgrades.

## Global Constraints

- Preserve current CLI/OpenCV behavior.
- Keep full-frame restricted-area behavior unchanged.
- Keep temporary BoT-SORT IDs unchanged.
- No polygon, dwell, incident, evidence, storage, or search modules in this refactor.
- Do not create unused interfaces, factories, or empty future packages.

## File boundaries

- `surveillance/config.py`: `.env` parsing and validated settings.
- `surveillance/models.py`: framework-free tracked-detection data.
- `surveillance/camera/droidcam.py`: OpenCV/MSMF camera lifecycle only.
- `surveillance/perception/yolo_tracker.py`: YOLO model and BoT-SORT integration only.
- `surveillance/rendering/opencv.py`: drawing and window display only.
- `surveillance/application/live_pipeline.py`: frame-loop orchestration only.
- `main.py`: composition root and dependency wiring only.

## Tasks

- [x] Move configuration and detection data into focused modules.
- [x] Extract camera, perception, rendering, and pipeline components.
- [x] Split tests by component boundary.
- [x] Run unit tests, compilation, lock check, and runtime model probe.
