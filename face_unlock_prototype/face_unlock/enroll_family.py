
import json
from pathlib import Path

import cv2
from face_engine import detect_largest_face, prepare_face

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "family_profiles"
PROFILES_FILE = DATA_DIR / "profiles.json"


def load_profiles():
    if not PROFILES_FILE.exists():
        return {}
    with open(PROFILES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_profiles(profiles):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROFILES_FILE, "w", encoding="utf-8") as file:
        json.dump(profiles, file, indent=4, ensure_ascii=False)


def main():
    profiles = load_profiles()

    name = input("Family member's name: ").strip()
    relationship = input("Relationship to patient: ").strip()
    greeting = input(
        "Personal greeting (optional): "
    ).strip()

    if not name or not relationship:
        print("Name and relationship are required.")
        return

    profile_id = str(max(
        [int(key) for key in profiles] or [0]
    ) + 1)

    profile_dir = DATA_DIR / profile_id
    profile_dir.mkdir(parents=True, exist_ok=True)

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("Cannot open webcam.")
        return

    count = 0
    target = 25

    print("\nKeep only this family member in view.")
    print("Press SPACE to save a face sample.")
    print("Press Q to finish enrollment.")

    while count < target:
        ok, frame = camera.read()
        if not ok:
            print("Could not read camera frame.")
            break

        box = detect_largest_face(frame)

        if box is not None:
            x, y, w, h = box
            cv2.rectangle(
                frame, (x, y), (x + w, y + h),
                (0, 255, 0), 2
            )
            cv2.putText(
                frame, f"Samples: {count}/{target}",
                (20, 35), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0, 255, 0), 2
            )
        else:
            cv2.putText(
                frame, "No face detected",
                (20, 35), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0, 0, 255), 2
            )

        cv2.imshow("Register Family Member", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        if key == 32 and box is not None:
            face = prepare_face(frame, box)
            if face is not None:
                filename = profile_dir / f"{count:03d}.png"
                if cv2.imwrite(str(filename), face):
                    count += 1
                    print(f"Saved sample {count}/{target}")

    camera.release()
    cv2.destroyAllWindows()

    if count < 5:
        print("Too few samples. Please enrol again.")
        return

    profiles[profile_id] = {
        "name": name,
        "relationship": relationship,
        "greeting": greeting or f"This is {name}, your {relationship}."
    }

    save_profiles(profiles)
    print(f"Registered {name} as profile {profile_id}.")


if __name__ == "__main__":
    main()