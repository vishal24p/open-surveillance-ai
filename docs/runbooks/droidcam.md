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

4. Confirm `Surveillance` window shows moving phone video, person boxes with temporary IDs when people are visible, and `People: N`. Press `Q` to close it.

To check incident recording, keep any people detected for at least two uninterrupted seconds. The console reports confirmation, then reports the saved clip after ten empty seconds. Each confirmed frame incident creates a numbered folder under `incidents/` containing `incident.mp4` and `incident.json`. Any person returning before the empty deadline continues the same clip; a return at or after the deadline requires a new two-second dwell and creates another folder.

## Pass

Real-person validation of the current frame-based architecture is pending. Earlier validation reports concern the preceding flow; they do not establish this release's detector accuracy.

- Phone image changes when phone moves.
- No green or blank window.
- Person detection runs when a person is visible.
- The same person keeps the same temporary ID across nearby frames.
- `People: N` appears in the top-right.
- `Q` closes window.
- A confirmed occupied frame produces `incident.mp4` and `incident.json` in its own numbered `incidents/` folder after ten empty seconds.
- Any person returning before the empty deadline stays in the current incident and clears the empty timer.
- Two people staying while a third enters/leaves produce one incident and clip; temporary IDs never split it.

Opening a camera is not a pass. OpenCV must successfully read real frames.

## Failures

| Symptom | Cause | Action |
| --- | --- | --- |
| Laptop webcam appears | Wrong index | Set `DROIDCAM_INDEX` in `.env` to DroidCam index. |
| Camera cannot open | Wrong index or DroidCam disconnected | Connect DroidCam and check `.env`. |
| Green/blank window or `OnReadSample` error | `DroidCam Video` virtual driver is not providing frames | Close other camera apps. If it persists, reinstall DroidCam Windows client, restart Windows, reconnect phone, and rerun this command. |

## Rules for future work

- Use `cv2.CAP_MSMF`; do not revert to `cv2.CAP_DSHOW` for DroidCam numeric indexes.
- Person detection, tracking, dwell confirmation, and evidence capture exist. Validate live camera and incident behavior on the target machine.
- V1 restricted area is the entire camera frame. The pre-roll is ten seconds before first detection; dwell confirms after two uninterrupted occupied seconds. The first empty frame starts the ten-second post-roll. Detection boxes and IDs are overlays only; configurable zones are future work.
- Evidence MP4s use 30 FPS with elapsed-time playback. Gaps repeat the previous image; captures above 30 FPS are dropped. Early shutdown saves incomplete metadata.
- Keep `DROIDCAM_INDEX` in local `.env`, never source control.
