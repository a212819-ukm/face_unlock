
import json
from pathlib import Path
from collections import deque, Counter

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

# Initial values only. Validate them with real test data.
MATCH_THRESHOLD = 55.0
UNCERTAIN_THRESHOLD = 70.0

CAMERA_INDEX = 0
RECOGNITION_INTERVAL = 3
STABLE_PREDICTIONS = 4
HISTORY_LENGTH = 6

WINDOW_NAME = "Remembrance - Live Family Recognition"


def load_profiles():
    if not PROFILES_FILE.exists():
        raise FileNotFoundError(
            "Family profiles not found. Run enroll_family.py first."
        )

    with open(PROFILES_FILE, "r", encoding="utf-8") as file:
        profiles = json.load(file)

    if not profiles:
        raise RuntimeError("No family profiles are registered.")

    return profiles


def train_recognizer(profiles):
    recognizer = create_recognizer()
    images = []
    labels = []

    for profile_id in profiles:
        folder = DATA_DIR / str(profile_id)

        if not folder.exists():
            continue

        for path in folder.glob("*.png"):
            image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)

            if image is not None and image.shape == (200, 200):
                images.append(image)
                labels.append(int(profile_id))

    if not images:
        raise RuntimeError("No valid enrolled face samples were found.")

    recognizer.train(
        images,
        np.asarray(labels, dtype=np.int32),
    )

    print(
        f"Loaded {len(images)} samples from "
        f"{len(set(labels))} family profile(s)."
    )

    return recognizer


def classify_face(face, recognizer, profiles):
    profile_id, distance = recognizer.predict(face)
    profile = profiles.get(str(profile_id))

    if profile is not None and distance <= MATCH_THRESHOLD:
        return {
            "status": "recognised",
            "profile_id": str(profile_id),
            "name": profile.get("name", "Family member"),
            "relationship": profile.get("relationship", "family member"),
            "greeting": profile.get(
                "greeting", "Hello. I am happy to see you."
            ),
            "distance": float(distance),
        }

    if distance <= UNCERTAIN_THRESHOLD:
        return {
            "status": "uncertain",
            "distance": float(distance),
        }

    return {
        "status": "unknown",
        "distance": float(distance),
    }


def choose_stable_result(history):
    """Show an identity only after repeated consistent predictions."""

    if len(history) < STABLE_PREDICTIONS:
        return None

    recent = list(history)[-STABLE_PREDICTIONS:]

    recognised = [
        item for item in recent
        if item["status"] == "recognised"
    ]

    if len(recognised) < STABLE_PREDICTIONS:
        return None

    ids = [item["profile_id"] for item in recognised]
    most_common_id, count = Counter(ids).most_common(1)[0]

    if count < STABLE_PREDICTIONS:
        return None

    matching = [
        item for item in recognised
        if item["profile_id"] == most_common_id
    ]

    # Use the lowest distance among the matching predictions.
    return min(matching, key=lambda item: item["distance"])


def draw_popup(frame, result, message):
    """Draw a large translucent message over the live camera view."""

    height, width = frame.shape[:2]

    panel_width = min(width - 32, 680)
    panel_height = min(230, max(150, height // 3))

    x1 = (width - panel_width) // 2
    y1 = max(20, height // 2 - panel_height // 2 + 100)
    x2 = x1 + panel_width
    y2 = min(height - 65, y1 + panel_height)

    # Keep a margin around the popup.
    y1 = min(y1, y2 - panel_height)

    overlay = frame.copy()

    if result and result["status"] == "recognised":
        panel_colour = (90, 115, 75)
        title = f"This looks like {result['name']}"
        subtitle = f"Your {result['relationship']}"
        greeting = result["greeting"]
    else:
        panel_colour = (65, 85, 95)
        title = message
        subtitle = "Please try again or ask your caregiver."
        greeting = ""

    cv2.rectangle(
        overlay, (x1, y1), (x2, y2), panel_colour, -1
    )

    # Blend the panel with the live camera image.
    cv2.addWeighted(overlay, 0.78, frame, 0.22, 0, frame)

    def draw_centered(text, y, scale, colour, thickness=2):
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(
            text, font, scale, thickness
        )[0]

        # Shrink long text to fit the panel.
        while text_size[0] > panel_width - 32 and scale > 0.42:
            scale -= 0.04
            text_size = cv2.getTextSize(
                text, font, scale, thickness
            )[0]

        x = max(8, (width - text_size[0]) // 2)
        cv2.putText(
            frame, text, (x, y), font, scale,
            colour, thickness, cv2.LINE_AA
        )

    draw_centered(
        title, y1 + 48, 0.9, (245, 255, 255), 2
    )
    draw_centered(
        subtitle, y1 + 92, 0.65, (255, 255, 255), 2
    )

    if greeting:
        # Keep the popup readable by limiting the greeting length.
        greeting = greeting.strip()
        if len(greeting) > 65:
            greeting = greeting[:62].rsplit(" ", 1)[0] + "..."

        draw_centered(
            greeting, y1 + 135, 0.55, (255, 255, 255), 2
        )


def main():
    profiles = load_profiles()
    recognizer = train_recognizer(profiles)

    camera = cv2.VideoCapture(CAMERA_INDEX)

    if not camera.isOpened():
        raise RuntimeError(
            "Cannot open webcam. Check camera permissions or CAMERA_INDEX."
        )

    history = deque(maxlen=HISTORY_LENGTH)
    frame_number = 0
    last_result = None
    last_status = "Searching for a face..."
    last_boxes = []

    print("\nRemembrance: Live Family Recognition")
    print("Q or ESC: Exit")
    print("Recognition runs locally on your computer.")
    print("The camera frames are not saved as video.")

    try:
        while True:
            ok, frame = camera.read()

            if not ok:
                print("Could not read camera frame.")
                break

            frame_number += 1
            boxes = detect_all_faces(frame)
            last_boxes = boxes

            # Choose the largest detected face for the popup.
            primary_box = None

            if boxes:
                primary_box = max(
                    boxes,
                    key=lambda b: int(b[2]) * int(b[3])
                )

            if primary_box is None:
                history.clear()
                last_result = None
                last_status = "Looking for your family member..."

            elif frame_number % RECOGNITION_INTERVAL == 0:
                face = prepare_face(frame, tuple(map(int, primary_box)))

                if face is not None:
                    prediction = classify_face(
                        face, recognizer, profiles
                    )
                    history.append(prediction)

                    stable_result = choose_stable_result(history)

                    if stable_result is not None:
                        last_result = stable_result
                        last_status = "Family member recognised"
                    else:
                        # Never retain an old person's identity when
                        # recent predictions no longer support it.
                        last_result = None

                        statuses = [
                            item["status"] for item in history
                        ]

                        if statuses and all(
                            status == "unknown" for status in statuses
                        ):
                            last_status = "I don't recognise this person."
                        else:
                            last_status = "I'm not sure who this is."

            # Draw boxes on every detected face.
            for box in boxes:
                x, y, w, h = map(int, box)

                is_primary = box is primary_box
                colour = (
                    (60, 210, 90)
                    if is_primary and last_result is not None
                    else (220, 210, 80)
                )

                cv2.rectangle(
                    frame, (x, y), (x + w, y + h), colour, 3
                )

            draw_popup(frame, last_result, last_status)

            cv2.putText(
                frame,
                "Q / ESC - Exit",
                (18, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q") or key == 27:
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
