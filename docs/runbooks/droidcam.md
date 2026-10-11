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

To check incident recording, leave a tracked person visible for at least two seconds. The console reports confirmation, then reports the saved clip after the track is removed and the ten-second post-roll completes. Each confirmed incident creates a numbered folder under `incidents/` containing `incident.mp4` and `incident.json`. A same-track return during post-roll continues the same clip; a later incident creates another folder.

## Pass

The user reports completing real-world validation. The repository does not record a clip count or case-by-case results.

- Phone image changes when phone moves.
- No green or blank window.
- Person detection runs when a person is visible.
- The same person keeps the same temporary ID across nearby frames.
- `People: N` appears in the top-right.
- `Q` closes window.
- A confirmed track produces `incident.mp4` and `incident.json` in its own numbered `incidents/` folder after final track removal plus ten seconds.
- A same-track return during post-roll stays in the current incident and restarts the post-roll after its next exit.

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
- V1 restricted area is the entire camera frame. The pre-roll is ten seconds before first detection; dwell confirms after two seconds. The tracker preserves tracks through 30 missing frames and removes them on the next missed frame, then the ten-second post-roll starts. Detection boxes are overlays only; configurable zones are future work.
- Evidence MP4s use 30 FPS with elapsed-time playback. Gaps repeat the previous image; captures above 30 FPS are dropped. Early shutdown saves incomplete metadata.
- Keep `DROIDCAM_INDEX` in local `.env`, never source control.
