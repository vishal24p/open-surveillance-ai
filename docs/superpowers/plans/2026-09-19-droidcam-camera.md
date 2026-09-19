# DroidCam Camera Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Read DroidCam as a Windows virtual webcam with no RTSP path.

**Architecture:** `main.py` starts the camera. `surveillance/camera.py` reads one optional `DROIDCAM_INDEX` setting and opens that Windows DirectShow device through OpenCV.

**Tech Stack:** Python 3.11, OpenCV, standard library, uv.

**Spec:** `HANDOFF.md` plus the user's DroidCam-only instruction.

## Global Constraints

- Python 3.11 with `uv`.
- Keep the first slice CLI/OpenCV-based.
- Input is DroidCam over USB; remove RTSP support.
- Runtime dependency set remains `opencv-python` only.
- Do not add detection, tracking, VLMs, databases, cloud APIs, or a web UI.

## Review Focus

- Default camera index is `0`.
- A non-negative `DROIDCAM_INDEX` overrides the default.
- Invalid indexes explain how to fix the configuration.
- An unopened Windows camera releases resources and reports the index.
- Manual USB validation remains required because hardware is external.

---

### Task 1: DroidCam Virtual Camera

**Files:**
- Modify: `surveillance/camera.py`
- Modify: `main.py`
- Modify: `tests/test_camera.py`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `HANDOFF.md`
- Delete: `.env.example`

**Interfaces:**
- Produces: `get_droidcam_index(environment: Mapping[str, str] | None = None) -> int`
- Produces: `show_droidcam(index: int) -> None`

- [x] **Step 1: Write failing tests for index selection**

```python
def test_default_index_is_zero():
    assert get_droidcam_index({}) == 0

def test_invalid_index_is_rejected():
    with self.assertRaisesRegex(RuntimeError, "DROIDCAM_INDEX"):
        get_droidcam_index({"DROIDCAM_INDEX": "-1"})
```

- [x] **Step 2: Run tests to verify they fail**

Run: `uv run python -m unittest discover -s tests -v`

Expected: FAIL because `get_droidcam_index` does not exist.

- [x] **Step 3: Replace RTSP code with DroidCam code**

```python
def get_droidcam_index(environment=None) -> int:
    value = (os.environ if environment is None else environment).get("DROIDCAM_INDEX", "0")
    index = int(value)
    if index < 0:
        raise RuntimeError("DROIDCAM_INDEX must be a non-negative integer.")
    return index

def show_droidcam(index: int) -> None:
    camera = cv2.VideoCapture(index, cv2.CAP_DSHOW)
```

- [x] **Step 4: Run checks**

Run: `uv run python -m unittest discover -s tests -v; uv run python -m py_compile main.py surveillance\\camera.py`

Expected: tests and compilation pass.

- [ ] **Step 5: Manually validate DroidCam**

Run: `uv run python main.py`

Expected: DroidCam window opens. If Windows assigns another device index, run `$env:DROIDCAM_INDEX=1` before the command.
