# DroidCam Media Foundation Fix Plan

**Goal:** Open DroidCam index `1` through OpenCV's working Windows backend.

**Root cause:** DirectShow opens the HP webcam at index `0` but fails for DroidCam at index `1`; the same index opens with Media Foundation.

**Change:** Replace `cv2.CAP_DSHOW` with `cv2.CAP_MSMF` in `show_droidcam`.

**Verification:** Run the existing test suite, compile the camera files, and confirm a read-only OpenCV probe opens index `1` with `CAP_MSMF`.
