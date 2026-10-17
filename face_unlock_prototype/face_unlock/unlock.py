"""Run the webcam and compare detected faces with the enrolled LBPH model."""
import json
from pathlib import Path
import cv2

from face_engine import detect_largest_face, prepare_face, create_recognizer

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
MODEL_PATH = DATA / "face_model.yml"
INFO_PATH = DATA / "profile.json"

# LBPH returns a distance, where lower generally means a closer match.
# This is only a starter threshold. Calibrate it with genuine and impostor tests.
STARTER_THRESHOLD = 65.0


def main():
    if not MODEL_PATH.exists() or not INFO_PATH.exists():
        print("No enrolled profile found. Run: python enroll.py")
        return

    profile = json.loads(INFO_PATH.read_text(encoding="utf-8"))
    recognizer = create_recognizer()
    recognizer.read(str(MODEL_PATH))

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open webcam. Check camera permissions or try VideoCapture(1).")
        return

    print("Look at the camera. Press Q to quit.")
    print("For this demo, a match only reveals a message inside this prototype.")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            box = detect_largest_face(frame)
            preview = frame.copy()
            status = "LOCKED"
            color = (0, 0, 255)

            if box is not None:
                face = prepare_face(frame, box)
                if face is not None:
                    label, distance = recognizer.predict(face)
                    if distance < STARTER_THRESHOLD:
                        status = f"ACCESS GRANTED: {profile['name']} (demo)"
                        color = (0, 200, 0)
                    else:
                        status = f"ACCESS DENIED (distance {distance:.1f})"
                    x, y, w, h = box
                    cv2.rectangle(preview, (x, y), (x + w, y + h), color, 2)

            cv2.putText(preview, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.62, color, 2)
            cv2.putText(preview, "Q = quit | Demo only, no liveness protection",
                        (10, preview.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.imshow("Face Unlock - demo", preview)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
