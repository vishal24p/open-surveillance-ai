# DroidCam Env File Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Configure the DroidCam camera index from local `.env` before opening the camera.

**Architecture:** `surveillance/camera.py` reads only `DROIDCAM_INDEX` from `.env`. `main.py` remains the entry point; `.env.example` gives the mobile-camera default.

**Tech Stack:** Python 3.11, standard library, OpenCV, uv.

**Spec:** User request: “make that in the env file … code have to look for that file before running.”

## Global Constraints

- DroidCam USB only; no RTSP support.
- Do not add a dotenv dependency.
- `.env` is local and ignored by Git.
- Default DroidCam index in the example is `1`.

## Review Focus

- A valid `.env` value opens that index.
- Missing `.env` gives a setup error instead of opening the laptop camera.
- Missing or invalid `DROIDCAM_INDEX` gives a clear error.
- A negative index is rejected before OpenCV opens a device.

---

### Task 1: Read DroidCam Index from .env

**Files:**
- Create: `.env.example`
- Modify: `surveillance/camera.py`
- Modify: `tests/test_camera.py`
- Modify: `README.md`
- Modify: `AGENTS.md`

**Interfaces:**
- Produces: `get_droidcam_index(env_path: Path = Path('.env')) -> int`

- [x] **Step 1: Write failing file-configuration tests**

```python
def test_env_file_index_is_used():
    env_path.write_text("DROIDCAM_INDEX=1\n")
    self.assertEqual(get_droidcam_index(env_path), 1)

def test_missing_env_file_is_rejected():
    with self.assertRaisesRegex(RuntimeError, ".env"):
        get_droidcam_index(env_path)
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run python -m unittest discover -s tests -v`

Expected: FAIL because the current function expects an environment mapping, not a file path.

- [x] **Step 3: Implement the standard-library `.env` reader**

```python
def get_droidcam_index(env_path: Path = Path(".env")) -> int:
    value = _read_env_value(env_path, "DROIDCAM_INDEX")
    return _validate_camera_index(value)
```

- [x] **Step 4: Run checks**

Run: `uv run python -m unittest discover -s tests -v; uv run python -m py_compile main.py surveillance\\camera.py`

Expected: tests and compilation pass.

- [ ] **Step 5: Add local configuration**

Run: `Copy-Item .env.example .env; uv run python main.py`

Expected: DroidCam at index `1` opens. Do not commit `.env`.
