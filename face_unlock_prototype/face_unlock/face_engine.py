
from pathlib import Path

import cv2
import numpy as np

# Look for the cascade file in the project folder first.
LOCAL_CASCADE = (
    Path(__file__).resolve().parent
    / "haarcascade_frontalface_default.xml"
)

# Use OpenCV's bundled copy if available.
BUNDLED_CASCADE = (
    Path(cv2.data.haarcascades)
    / "haarcascade_frontalface_default.xml"
)


def load_face_detector():
    """Load the Haar Cascade face detection model."""

    if LOCAL_CASCADE.is_file():
        cascade_path = str(LOCAL_CASCADE)
    elif BUNDLED_CASCADE.is_file():
        cascade_path = str(BUNDLED_CASCADE)
    else:
        raise FileNotFoundError(
            "Face detection model not found.\n"
            f"Expected local file: {LOCAL_CASCADE}\n"
            f"Checked OpenCV file: {BUNDLED_CASCADE}\n"
            "Download haarcascade_frontalface_default.xml "
            "and place it beside face_engine.py."
        )

    detector = cv2.CascadeClassifier(cascade_path)

    if detector.empty():
        raise RuntimeError(
            f"OpenCV could not load the cascade file: {cascade_path}"
        )

    print(f"Face detector loaded: {cascade_path}")
    return detector


# Load the detector once, rather than once per camera frame.
FACE_DETECTOR = load_face_detector()


def detect_largest_face(frame):
    """Return the largest face as (x, y, w, h), or None."""

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = FACE_DETECTOR.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(100, 100)
    )

    if len(faces) == 0:
        return None

    return max(
        faces,
        key=lambda face: face[2] * face[3]
    )


def detect_all_faces(frame):
    """Return every detected face as (x, y, w, h)."""

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = FACE_DETECTOR.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80)
    )

    return list(faces)


def prepare_face(frame, box, size=(200, 200)):
    """Crop a detected face, convert it to grayscale and resize it."""

    x, y, w, h = box

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    margin_x = int(w * 0.12)
    margin_y = int(h * 0.12)

    x1 = max(0, x - margin_x)
    y1 = max(0, y - margin_y)
    x2 = min(gray.shape[1], x + w + margin_x)
    y2 = min(gray.shape[0], y + h + margin_y)

    crop = gray[y1:y2, x1:x2]

    if crop.size == 0:
        return None

    return cv2.resize(
        crop,
        size,
        interpolation=cv2.INTER_AREA
    )


def create_recognizer():
    """Create OpenCV's LBPH face recognizer."""

    if not hasattr(cv2, "face"):
        raise RuntimeError(
            "cv2.face is unavailable. Install "
            "opencv-contrib-python and restart Python."
        )

    return cv2.face.LBPHFaceRecognizer_create()