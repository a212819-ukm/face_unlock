
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

# Initial conservative settings. Validate these with real test samples.
MATCH_THRESHOLD = 55.0
UNCERTAIN_THRESHOLD = 70.0

CAMERA_WINDOW = "Remembrance - Family Recognition"
RESULT_WINDOW = "Remembrance - Family Memory Aid"


def load_profiles():
    if not PROFILES_FILE.exists():
        raise FileNotFoundError(
            "No family profiles found. "
            "Run enroll_family.py first."
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
            image = cv2.imread(
                str(path), cv2.IMREAD_GRAYSCALE
            )

            if image is not None:
                images.append(image)
                labels.append(int(profile_id))

    if not images:
        raise RuntimeError(
            "No face samples found. Register family members first."
        )

    recognizer.train(
        images,
        np.asarray(labels, dtype=np.int32)
    )

    print(
        f"Loaded {len(images)} face samples "
        f"from {len(set(labels))} profile(s)."
    )

    return recognizer


def classify_face(face, recognizer, profiles):
    """Classify a face conservatively."""

    profile_id, distance = recognizer.predict(face)

    # A smaller LBPH distance generally indicates a closer match.
    if distance <= MATCH_THRESHOLD:
        profile = profiles.get(str(profile_id))

        if profile is not None:
            return {
                "status": "recognised",
                "name": profile.get("name", "Family member"),
                "relationship": profile.get(
                    "relationship", "Family member"
                ),
                "greeting": profile.get(
                    "greeting",
                    "Hello. I am happy to see you."
                ),
                "distance": distance,
            }

    if distance <= UNCERTAIN_THRESHOLD:
        return {
            "status": "uncertain",
            "distance": distance,
        }

    return {
        "status": "unknown",
        "distance": distance,
    }


def analyse_snapshot(frame, recognizer, profiles):
    """Recognise each detected face in one camera snapshot."""

    results = []
    boxes = detect_all_faces(frame)

    for box in boxes:
        x, y, w, h = map(int, box)
        face = prepare_face(frame, (x, y, w, h))

        if face is None:
            continue

        result = classify_face(face, recognizer, profiles)
        results.append(result)

        if result["status"] == "recognised":
            label = result["name"]
            colour = (0, 160, 0)
        elif result["status"] == "uncertain":
            label = "Not sure - try again"
            colour = (0, 165, 255)
        else:
            label = "Not recognised"
            colour = (0, 0, 220)

        cv2.rectangle(
            frame, (x, y), (x + w, y + h), colour, 3
        )

        cv2.putText(
            frame,
            label,
            (x, max(30, y - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            colour,
            2,
            cv2.LINE_AA,
        )

    return frame, results


def wrap_text(text, max_chars=48):
    """Wrap ordinary text for the result screen."""

    words = str(text).split()
    lines = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()

        if len(candidate) > max_chars and current:
            lines.append(current)
            current = word
        else:
            current = candidate

    if current:
        lines.append(current)

    return lines


def put_lines(canvas, lines, x, y, font_scale=0.8,
              colour=(40, 40, 40), thickness=2,
              line_height=34):
    for line in lines:
        cv2.putText(
            canvas,
            line,
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            colour,
            thickness,
            cv2.LINE_AA,
        )
        y += line_height

    return y


def build_result_screen(frame, results, caregiver_help=False):
    """Create a large, readable result screen."""

    width, height = 1100, 850
    canvas = np.full((height, width, 3), 250, dtype=np.uint8)

    cv2.putText(
        canvas,
        "REMEMBRANCE",
        (35, 48),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.1,
        (45, 90, 80),
        3,
        cv2.LINE_AA,
    )

    cv2.putText(
        canvas,
        "Family recognition",
        (35, 88),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (70, 70, 70),
        2,
        cv2.LINE_AA,
    )

    # Show the captured image at the top.
    preview = cv2.resize(frame, (660, 370))
    canvas[110:480, 35:695] = preview

    # Put the identity information in a separate large-text panel.
    x = 725
    y = 130

    if caregiver_help:
        put_lines(
            canvas,
            ["Please ask your caregiver", "to help identify this person."],
            x, y,
            font_scale=0.75,
            colour=(50, 50, 50),
            line_height=38,
        )

    elif not results:
        put_lines(
            canvas,
            ["I could not find a clear face.",
             "Please try again."],
            x, y,
            font_scale=0.75,
            colour=(50, 50, 50),
            line_height=38,
        )

    else:
        # Each visible face receives its own result.
        for index, result in enumerate(results[:3]):
            y = 125 if index == 0 else y + 12

            if result["status"] == "recognised":
                name = result["name"]
                relationship = result["relationship"]
                greeting = result["greeting"]

                y = put_lines(
                    canvas,
                    [name],
                    x, y,
                    font_scale=0.9,
                    colour=(35, 105, 65),
                    thickness=2,
                    line_height=40,
                )

                y = put_lines(
                    canvas,
                    [f"Your {relationship}"],
                    x, y,
                    font_scale=0.58,
                    colour=(55, 55, 55),
                    thickness=2,
                    line_height=30,
                )

                y = put_lines(
                    canvas,
                    wrap_text(greeting, 38),
                    x, y + 5,
                    font_scale=0.48,
                    colour=(55, 55, 55),
                    thickness=1,
                    line_height=25,
                )

            elif result["status"] == "uncertain":
                y = put_lines(
                    canvas,
                    ["I'm not sure who this is."],
                    x, y,
                    font_scale=0.55,
                    colour=(0, 110, 170),
                    line_height=28,
                )

                y = put_lines(
                    canvas,
                    ["Please try again or ask your caregiver."],
                    x, y,
                    font_scale=0.43,
                    colour=(60, 60, 60),
                    thickness=1,
                    line_height=23,
                )

            else:
                y = put_lines(
                    canvas,
                    ["I don't recognise this person."],
                    x, y,
                    font_scale=0.52,
                    colour=(40, 40, 180),
                    line_height=28,
                )

                y = put_lines(
                    canvas,
                    ["You can try again or ask for help."],
                    x, y,
                    font_scale=0.43,
                    colour=(60, 60, 60),
                    thickness=1,
                    line_height=23,
                )

            y += 12

    # Controls remain visible on every result screen.
    cv2.line(canvas, (35, 755), (1065, 755), (210, 210, 210), 2)

    put_lines(
        canvas,
        ["R - Try again     H - Ask caregiver for help     Q - Exit"],
        35, 795,
        font_scale=0.65,
        colour=(45, 45, 45),
        thickness=2,
        line_height=30,
    )

    return canvas


def show_result(frame, results):
    while True:
        screen = build_result_screen(frame, results)
        cv2.imshow(RESULT_WINDOW, screen)

        key = cv2.waitKey(0) & 0xFF

        if key == ord("r"):
            return "retry"

        if key == ord("h"):
            help_screen = build_result_screen(
                frame, results, caregiver_help=True
            )
            cv2.imshow(RESULT_WINDOW, help_screen)
            cv2.waitKey(0)
            return "retry"

        if key == ord("q"):
            return "quit"


def main():
    profiles = load_profiles()
    recognizer = train_recognizer(profiles)

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        raise RuntimeError("Cannot open webcam.")

    print("\nRemembrance Family Recognition")
    print("SPACE - Take a snapshot and identify faces")
    print("Q - Quit")

    try:
        while True:
            ok, frame = camera.read()

            if not ok:
                print("Could not read camera frame.")
                break

            cv2.putText(
                frame,
                "SPACE: Recognise Family | Q: Quit",
                (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

            cv2.imshow(CAMERA_WINDOW, frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            if key == 32:
                result_frame, results = analyse_snapshot(
                    frame.copy(), recognizer, profiles
                )

                if not results:
                    print("No usable faces detected.")
                else:
                    for result in results:
                        print(result)

                action = show_result(result_frame, results)

                if action == "quit":
                    break

    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
