
import json
from pathlib import Path

import cv2
import numpy as np

from face_engine import (
    detect_all_faces,
    prepare_face,
    create_recognizer,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "family_profiles"
PROFILES_FILE = DATA_DIR / "profiles.json"

# Initial experimental setting, not a validated security threshold.
LBPH_THRESHOLD = 70.0


def load_profiles():
    if not PROFILES_FILE.exists():
        raise FileNotFoundError(
            "No family profiles found. Run enroll_family.py first."
        )

    with open(PROFILES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def train_recognizer(profiles):
    recognizer = create_recognizer()
    images = []
    labels = []

    for profile_id in profiles:
        folder = DATA_DIR / profile_id

        if not folder.exists():
            continue

        for path in folder.glob("*.png"):
            image = cv2.imread(
                str(path), cv2.IMREAD_GRAYSCALE
            )

            if image is not None:
                images.append(image)
                labels.append(int(profile_id))

    if not images:
        raise RuntimeError(
            "No usable face samples found. Enrol family members first."
        )

    recognizer.train(
        images,
        np.array(labels, dtype=np.int32)
    )
    print(
        f"Recognition model trained with {len(images)} samples "
        f"from {len(set(labels))} profile(s)."
    )
    return recognizer


def recognise_snapshot(frame, recognizer, profiles):
    boxes = detect_all_faces(frame)

    if len(boxes) == 0:
        cv2.putText(
            frame, "No face detected. Try again.",
            (20, 35), cv2.FONT_HERSHEY_SIMPLEX,
            0.7, (0, 0, 255), 2
        )
        return frame

    for box in boxes:
        x, y, w, h = map(int, box)
        face = prepare_face(frame, (x, y, w, h))

        if face is None:
            continue

        profile_id, distance = recognizer.predict(face)

        if (
            distance <= LBPH_THRESHOLD
            and str(profile_id) in profiles
        ):
            profile = profiles[str(profile_id)]
            name = profile["name"]
            relationship = profile["relationship"]

            label = f"{name} - {relationship}"
            colour = (0, 180, 0)

            print(
                f"Recognised: {name} ({relationship}); "
                f"LBPH distance={distance:.1f}"
            )
        else:
            label = "Not recognised"
            colour = (0, 0, 255)
            print(
                f"Face not recognised; "
                f"LBPH distance={distance:.1f}"
            )

        cv2.rectangle(
            frame, (x, y), (x + w, y + h), colour, 2
        )

        # Keep the label readable when it is long.
        label_y = max(25, y - 10)
        cv2.putText(
            frame, label, (x, label_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55,
            colour, 2
        )

    return frame


def main():
    profiles = load_profiles()
    recognizer = train_recognizer(profiles)

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        raise RuntimeError("Cannot open webcam.")

    print("\nRemembrance Family Recognition")
    print("SPACE: identify faces in a snapshot")
    print("Q: quit")
    print("For enrollment, register each family member separately.")

    while True:
        ok, frame = camera.read()

        if not ok:
            print("Could not read camera frame.")
            break

        cv2.putText(
            frame, "SPACE: Recognise Family | Q: Quit",
            (15, 30), cv2.FONT_HERSHEY_SIMPLEX,
            0.65, (0, 255, 0), 2
        )

        cv2.imshow("Remembrance - Family Recognition", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        if key == 32:
            result = recognise_snapshot(
                frame.copy(), recognizer, profiles
            )

            cv2.imshow(
                "Recognition Results - Press any key to continue",
                result
            )

            result_key = cv2.waitKey(0) & 0xFF

            result_window = (
                "Recognition Results - Press any key to continue"
            )

            # Close the window only if it still exists.
            if cv2.getWindowProperty(
                result_window, cv2.WND_PROP_VISIBLE
            ) >= 1:
                cv2.destroyWindow(result_window)

            if result_key == ord("q"):
                break

                camera.release()
                cv2.destroyAllWindows()


if __name__ == "__main__":
    main()