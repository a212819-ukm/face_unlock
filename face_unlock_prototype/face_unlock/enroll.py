"""Enroll one person's face from several live webcam frames."""
import json
from pathlib import Path
import cv2
import numpy as np

from face_engine import detect_largest_face, prepare_face, create_recognizer

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
MODEL_PATH = DATA / "face_model.yml"
INFO_PATH = DATA / "profile.json"


def main():
    name = input("Enter a short profile name (do not use a password): ").strip()
    if not name:
        print("A profile name is required.")
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open webcam. Check camera permissions or try VideoCapture(1).")
        return

    samples = []
    print("Look at the camera. Press SPACE to capture a face sample.")
    print("Capture 20-30 samples: front, slightly left, slightly right, and different lighting.")
    print("Press Q to quit. Keep only one person's face in the frame.")

    try:
        while len(samples) < 30:
            ok, frame = cap.read()
            if not ok:
                print("Could not read from webcam.")
                break

            box = detect_largest_face(frame)
            preview = frame.copy()
            if box is not None:
                x, y, w, h = box
                cv2.rectangle(preview, (x, y), (x + w, y + h), (0, 220, 0), 2)
                cv2.putText(preview, "Face detected - SPACE to capture",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 0), 2)
            else:
                cv2.putText(preview, "No face detected", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)

            cv2.putText(preview, f"Samples: {len(samples)}/30 | Q = quit",
                        (10, preview.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
            cv2.imshow("Face enrollment", preview)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break
            if key == ord(" ") and box is not None:
                face = prepare_face(frame, box)
                if face is not None:
                    samples.append(face)
                    print(f"Captured sample {len(samples)}/30")
    finally:
        cap.release()
        cv2.destroyAllWindows()

    if len(samples) < 5:
        print("Not enough samples. Please enrol again and capture at least 5.")
        return

    recognizer = create_recognizer()
    labels = np.zeros(len(samples), dtype=np.int32)
    recognizer.train(samples, labels)
    recognizer.write(str(MODEL_PATH))
    INFO_PATH.write_text(json.dumps({"name": name}, indent=2), encoding="utf-8")
    print(f"Enrollment saved for '{name}'. Samples captured: {len(samples)}")
    print("Note: this is a learning demo, not secure authentication.")


if __name__ == "__main__":
    main()
