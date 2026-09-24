# DroidCam

## Purpose

Prove that Android phone video reaches OpenCV and the current person-detection runner receives usable frames.

## Start

1. Connect phone to DroidCam Client over USB.
2. Confirm DroidCam Client shows moving phone video.
3. Run:

   ```powershell
   uv run python main.py
   ```

4. Confirm `DroidCam` window shows moving phone video, person boxes with temporary IDs when people are visible, and `People: N`. Press `Q` to close it.

## Pass

- Phone image changes when phone moves.
- No green or blank window.
- Person detection runs when a person is visible.
- The same person keeps the same temporary ID across nearby frames.
- `People: N` appears in the top-right.
- `Q` closes window.

Opening a camera is not a pass. OpenCV must successfully read real frames.

## Failures

| Symptom | Cause | Action |
| --- | --- | --- |
| Laptop webcam appears | Wrong index | Set `DROIDCAM_INDEX` in `.env` to DroidCam index. |
| Camera cannot open | Wrong index or DroidCam disconnected | Connect DroidCam and check `.env`. |
| Green/blank window or `OnReadSample` error | `DroidCam Video` virtual driver is not providing frames | Close other camera apps. If it persists, reinstall DroidCam Windows client, restart Windows, reconnect phone, and rerun this command. |

## Rules for future work

- Use `cv2.CAP_MSMF`; do not revert to `cv2.CAP_DSHOW` for DroidCam numeric indexes.
- Person detection already exists. Do not add tracking, configurable polygons, evidence, search, cloud services, or a web UI until this check passes on target machine.
- Current restricted area is the entire camera frame. Detection boxes are overlays only; custom zone boundaries are future work.
- Keep `DROIDCAM_INDEX` in local `.env`, never source control.
