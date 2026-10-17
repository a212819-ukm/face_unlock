# Face Unlock learning prototype

This repository contains two separate prototypes:

- A Python webcam demo using OpenCV Haar-cascade face detection and LBPH face matching.
- An Android Flutter app with a family-recognition camera preview and visual states.

This is an educational prototype, not phone-grade authentication. LBPH is lighting-sensitive, there is no liveness detection, and a photo or screen replay may fool it. Do not use it to protect private, financial, medical, or otherwise sensitive information.

## Run the Flutter Android app

Install the Flutter SDK and Android tooling (Android Studio with an emulator, or a physical Android phone with USB debugging enabled). From the repository root, change into the Flutter app folder:

```sh
cd face_unlock/face_unlock_prototype
flutter pub get
flutter run
```

The app opens to a home page; tap **OPEN FAMILY RECOGNITION** to open the front-camera preview. Android requests camera permission when needed. You can run the app on a connected phone or start an emulator first. Check available devices with `flutter devices`.

The Flutter screen currently provides the camera preview and recognition-result UI only. It does **not** run face recognition or load the Python enrollment data; that requires a separate compatible on-device recognition model and migration or re-enrollment work.

Run Flutter checks from the same folder:

```sh
flutter analyze
flutter test
```

## Requirements

- Python 3
- A webcam
- Windows, macOS, or Linux

The commands below use Python's built-in `venv` module. On Windows, install Python from [python.org](https://www.python.org/downloads/) or the Microsoft Store. During installation from python.org, enable **Add Python to PATH**.

## Get the project

Clone the repository, then enter the project directory:

```sh
git clone https://github.com/a212819-ukm/face_unlock.git
cd face_unlock/face_unlock_prototype
```

If you downloaded a ZIP instead, extract it and open a terminal in the `face_unlock_prototype` folder—the folder containing `requirements.txt`.

## Create an environment and install dependencies

Create a virtual environment in the project folder:

```sh
python -m venv .venv
```

On Windows, activate it in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

```bat
.\.venv\Scripts\activate.bat
```

On macOS or Linux, activate it with:

```sh
source .venv/bin/activate
```

Then install the project dependencies:

```sh
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The requirements install `opencv-contrib-python`, which includes `cv2.face` for LBPH recognition. Use this OpenCV package on its own; do not install `opencv-python` alongside it in the same environment.

## Try the single-person unlock demo

Run these commands from the `face_unlock_prototype` folder, with the virtual environment activated.

First, enroll a face:

```sh
python face_unlock/enroll.py
```

Enter a short profile name, then press **SPACE** to capture at least 5 face samples (20–30 are recommended). Look forward and slightly left and right, with ordinary variation in lighting. Press **Q** to finish early.

Next, test recognition:

```sh
python face_unlock/unlock.py
```

Try the enrolled person and another person. Press **Q** to quit. The displayed result is only a demo; the starter threshold of `65.0` is not universal and should not be treated as a security guarantee.

## Try family recognition instead

To enroll a family member, or add more samples to an existing profile, run:

```sh
python face_unlock/enroll_family.py
```

If profiles already exist, enter a profile ID to add samples to that person, or press **Enter** to create a new profile. For a new profile, provide the person's name and relationship. Press **SPACE** to capture at least 5 new samples (25 are recommended); vary head angle and distance slightly. The script appends samples to the selected profile instead of creating a duplicate. To recognize enrolled family members, run:

```sh
python face_unlock/recognize_family.py
```

Press **SPACE** to identify faces in a snapshot and **Q** to quit.

## Local profile data

Enrollment creates files under `face_unlock/data/` on your computer:

- `profile.json` and `face_model.yml` for the single-person demo.
- `family_profiles/` with face sample images and profile details for family recognition.

These are personal biometric data and are intentionally excluded from Git. Each person testing the project should enroll their own profiles locally; the repository does not include sample face data. Delete `face_unlock/data/` to remove locally stored profiles.

## Troubleshooting

- **The webcam will not open:** close other apps using it and check your operating system's camera permissions. The scripts use camera index `0`; if your webcam has a different index, update `cv2.VideoCapture(0)` in the relevant script.
- **`cv2.face` is unavailable:** activate the project's virtual environment and reinstall from `requirements.txt`. Check that you have not also installed `opencv-python` in that environment.
- **No face is detected:** improve lighting, face the camera, move closer, and make sure the whole face is visible.

## What the main functions do

- `VideoCapture(0)`: opens the default webcam.
- `detectMultiScale(...)`: finds candidate face regions.
- `prepare_face(...)`: crops the face, converts it to grayscale, and resizes it.
- `LBPHFaceRecognizer.train(...)`: builds a simple face recognizer from enrolled samples.
- `recognizer.predict(...)`: returns a predicted label and distance.
- `imshow(...)` and `waitKey(...)`: show the camera preview and read keyboard input.

## Next development stage

Replace LBPH with an appropriately licensed pretrained model, add liveness checks, and implement a mobile UI. For a production mobile app, prefer platform authentication APIs (Android BiometricPrompt and Apple's LocalAuthentication) when the goal is to authenticate the device owner.
