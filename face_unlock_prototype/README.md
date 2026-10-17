# Face Unlock learning prototype

A webcam-based learning demo using OpenCV Haar-cascade face detection and LBPH face matching.

## Important limitations
- This is an educational prototype, not phone-grade authentication.
- LBPH is an older, lighting-sensitive method and is not a modern deep-learning face embedding model.
- It has no liveness detection. A printed photo or screen replay may fool it.
- The distance threshold is only a starting point and must be calibrated with testing.
- Do not use it to protect private, financial, medical, or otherwise sensitive information.
- Enrolled face data is stored locally under `face_unlock/data/`. Delete that folder to remove the profile.

## 1. Create a virtual environment

Windows PowerShell, from this folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip uninstall -y opencv-python
pip install opencv-contrib-python
```

If PowerShell blocks activation, use Command Prompt:

```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
pip uninstall -y opencv-python
pip install opencv-contrib-python
```

Use only one OpenCV wheel (`opencv-contrib-python`) in this environment because it includes `cv2.face`.

## 2. Enrol a face

```powershell
cd face_unlock
python enroll.py
```

Type a profile name. Capture 20-30 samples by pressing SPACE while looking front, slightly left and slightly right. Press Q to stop early. Aim for varied, ordinary lighting.

## 3. Test unlocking

```powershell
python unlock.py
```

Try the enrolled person, then a different person. Observe the displayed LBPH distance. Lower values generally mean a closer match, but the threshold `65.0` is not universal. To adjust it, edit `STARTER_THRESHOLD` in `unlock.py` only after collecting test results.

## What the main functions do
- `VideoCapture(0)`: opens the default webcam.
- `detectMultiScale(...)`: finds candidate face regions.
- `prepare_face(...)`: crops the face, converts to grayscale and resizes it.
- `LBPHFaceRecognizer.train(...)`: builds a simple face recognizer from enrolled samples.
- `recognizer.predict(...)`: returns a predicted label and distance.
- `imshow(...)` and `waitKey(...)`: show the camera preview and read keyboard input.

## Next development stage
Replace LBPH with a pretrained deep-learning model such as an appropriately licensed ArcFace/InsightFace model, add liveness checks, and implement the mobile UI. For a production mobile app, prefer platform authentication APIs (Android BiometricPrompt and Apple's LocalAuthentication) when the goal is to authenticate the device owner.
