# Person Detection Smoke Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show person boxes, confidence, and a live people count on DroidCam video using the local GPU.

**Architecture:** Keep the existing CLI/OpenCV loop. Load one COCO-pretrained `yolo26s.pt` detector, request only class `person`, turn its returned boxes into simple tuples, then annotate the current frame before displaying it.

**Tech Stack:** Python 3.11, OpenCV, Ultralytics YOLO26s, PyTorch CUDA 13.0.

**Spec:** `MILESTONES.md` Milestone 1, step 1; confirmed user scope in this task.

## Global Constraints

- Python 3.11 and `uv` only.
- DroidCam remains an OpenCV/MSMF CLI window.
- Use `yolo26s.pt` on the RTX 4050; do not add tracking, zones, dwell timers, incidents, recordings, or storage.
- Show boxes/confidence and `People: N` in the top-right corner.
- Use only COCO class `person` and the explicit `PERSON_CONFIDENCE` cutoff in `.env`; no fallback is allowed.

## Review Focus

- Zero detections: render `People: 0` without error.
- Multiple detections: render one box/label per person and the correct count.
- Missing confidence setting: stop with a clear error; do not silently use a fallback.
- Low-confidence/non-person results: detector filtering must exclude them before counting.
- Model download/load failure: surface the library error; do not silently show a zero count.
- CUDA unavailable: fail explicitly rather than silently switching to CPU on this GPU-required smoke test.

---

### Task 1: Render and display people detections

**Files:**
- Modify: `pyproject.toml`
- Modify: `surveillance/camera.py`
- Modify: `tests/test_camera.py`
- Modify: `uv.lock`

**Interfaces:**
- Consumes: `show_droidcam(index: int) -> None`
- Produces: `draw_person_detections(frame, detections) -> None`, where each detection is `(x1, y1, x2, y2, confidence)`.

- [x] **Step 1: Write the failing rendering tests**

```python
def test_draw_person_detections_draws_box_and_count() -> None:
    frame = np.zeros((100, 200, 3), dtype=np.uint8)
    draw_person_detections(frame, [(20, 30, 80, 90, 0.91)])
    self.assertTrue(frame[30, 20].any())
    self.assertTrue(frame[:30, 100:].any())
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run python -m unittest discover -s tests -v`

Expected: FAIL because `draw_person_detections` does not exist.

- [x] **Step 3: Add the smallest detection implementation**

```python
model = YOLO("yolo26s.pt")
result = model(frame, classes=[0], conf=0.5, device=0, verbose=False)[0]
draw_person_detections(frame, detections_from(result))
```

Render each returned person with `cv2.rectangle` and `person 91%`; calculate `People: N` from the same detection list and place it at the top-right.

- [x] **Step 4: Add dependency and resolve environment**

Update `pyproject.toml` with `ultralytics>=8.4.77,<9`, plus the official PyTorch CUDA 13.0 index and direct `torch`/`torchvision` constraints, then run: `uv lock`

Run: `uv sync`

Expected: the lockfile contains Ultralytics and PyTorch dependencies.

- [x] **Step 5: Verify unit tests and GPU availability**

Run: `uv run python -m unittest discover -s tests -v`

Run: `uv run python -c "import torch; print(torch.cuda.get_device_name(0))"`

Expected: all tests PASS and output names the RTX 4050.

- [ ] **Step 6: Run live smoke test**

Run: `uv run python main.py`

Expected: first run downloads `yolo26s.pt`; live window shows person boxes/confidence and `People: N`; Q exits cleanly.

### Task 2: Configure the person-confidence cutoff

**Files:**
- Modify: `.env.example`
- Modify: `.env`
- Modify: `main.py`
- Modify: `surveillance/camera.py`
- Modify: `tests/test_camera.py`

**Interfaces:**
- Produces: `get_person_confidence(env_path: Path = Path(".env")) -> float`
- Changes: `show_droidcam(index: int, confidence: float) -> None`

- [x] **Step 1: Write failing configuration tests**

```python
def test_env_file_confidence_is_used(self) -> None:
    env_path.write_text("PERSON_CONFIDENCE=0.80\n", encoding="utf-8")
    self.assertEqual(get_person_confidence(env_path), 0.80)

def test_out_of_range_confidence_is_rejected(self) -> None:
    env_path.write_text("PERSON_CONFIDENCE=1.01\n", encoding="utf-8")
    with self.assertRaisesRegex(RuntimeError, "PERSON_CONFIDENCE"):
        get_person_confidence(env_path)
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run python -m unittest discover -s tests -v`

Expected: FAIL because `get_person_confidence` does not exist.

- [x] **Step 3: Add minimal parsing and wiring**

Reuse `_read_env_value`. Require `PERSON_CONFIDENCE`; parse it as a finite float from `0` to `1`, pass it from `main.py` into `show_droidcam`, and use it for YOLO's `conf` argument. Add `PERSON_CONFIDENCE=0.80` to both environment files.

- [x] **Step 4: Verify**

Run: `uv run python -m unittest discover -s tests -v`

Expected: all tests PASS.
