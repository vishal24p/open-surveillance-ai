# DroidCam

## Purpose

Prove that Android phone video reaches OpenCV before adding any surveillance module.

## Start

1. Connect phone to DroidCam Client over USB.
2. Confirm DroidCam Client shows moving phone video.
3. Run:

   ```powershell
   uv run python camera_test.py
   ```

4. Confirm `DroidCam` window shows moving phone video. Press `Q` to close it.

## Pass

- Phone image changes when phone moves.
- No green or blank window.
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
- Do not add detection, tracking, zones, evidence, search, cloud services, or a web UI until this check passes on target machine.
- Keep `DROIDCAM_INDEX` in local `.env`, never source control.
