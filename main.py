import cv2
import face_recognition
import os
import time
import numpy as np
from datetime import datetime
import csv

# -----------------------------------
# Load known faces
# -----------------------------------
known_encodings = []
known_names = []

KNOWN_FACES_DIR = "known_faces"

for file in os.listdir(KNOWN_FACES_DIR):

    path = os.path.join(KNOWN_FACES_DIR, file)

    img = face_recognition.load_image_file(path)

    encodings = face_recognition.face_encodings(img)

    # Skip bad images with no detectable face
    if len(encodings) > 0:
        known_encodings.append(encodings[0])

        # File name becomes person name
        name = os.path.splitext(file)[0]
        known_names.append(name)

    else:
        print(f"[WARNING] No face found in {file}")

# -----------------------------------
# Attendance setup
# -----------------------------------
marked_attendance = set()

today_date = datetime.now().strftime("%Y-%m-%d")

ATTENDANCE_DIR = "attendance"

# Create attendance folder if not exists
os.makedirs(ATTENDANCE_DIR, exist_ok=True)

csv_file = f"{ATTENDANCE_DIR}/{today_date}.csv"

# -----------------------------------
# Start webcam
# -----------------------------------
cap = cv2.VideoCapture(0)

process_this_frame = True

prev_time = 0

while True:

    ret, frame = cap.read()

    if not ret:
        print("Failed to access webcam")
        break

    # -----------------------------------
    # Resize frame for better FPS
    # -----------------------------------
    small_frame = cv2.resize(
        frame,
        (0, 0),
        fx=0.25,
        fy=0.25
    )

    rgb_small = cv2.cvtColor(
        small_frame,
        cv2.COLOR_BGR2RGB
    )

    # -----------------------------------
    # Process alternate frames
    # -----------------------------------
    if process_this_frame:

        face_locations = face_recognition.face_locations(rgb_small)

        face_encodings = face_recognition.face_encodings(
            rgb_small,
            face_locations
        )

        face_names = []

        for face_encoding in face_encodings:

            name = "Unknown"

            if len(known_encodings) > 0:

                distances = face_recognition.face_distance(
                    known_encodings,
                    face_encoding
                )

                best_match_index = np.argmin(distances)

                if distances[best_match_index] < 0.6:
                    name = known_names[best_match_index]

                    # -----------------------------------
                    # Mark attendance only once
                    # -----------------------------------
                    if name not in marked_attendance:

                        now = datetime.now()

                        current_date = now.strftime("%Y-%m-%d")
                        current_time = now.strftime("%H:%M:%S")

                        with open(csv_file, mode="a", newline="") as file:

                            writer = csv.writer(file)

                            # Add header if file empty
                            if file.tell() == 0:
                                writer.writerow(
                                    ["Name", "Date", "Time"]
                                )

                            writer.writerow(
                                [
                                    name,
                                    current_date,
                                    current_time
                                ]
                            )

                        marked_attendance.add(name)

                        print(f"{name} attendance marked")

            face_names.append(name)

    process_this_frame = not process_this_frame

    # -----------------------------------
    # Draw results
    # -----------------------------------
    for (top, right, bottom, left), name in zip(
        face_locations,
        face_names
    ):

        # Scale back face locations
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Rectangle around face
        cv2.rectangle(
            frame,
            (left, top),
            (right, bottom),
            (0, 255, 0),
            2
        )

        # Name label
        cv2.putText(
            frame,
            name,
            (left, top - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    # -----------------------------------
    # FPS calculation
    # -----------------------------------
    current_time = time.time()

    fps = (
        1 / (current_time - prev_time)
        if prev_time != 0 else 0
    )

    prev_time = current_time

    cv2.putText(
        frame,
        f"FPS: {int(fps)}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 0, 255),
        2
    )

    # -----------------------------------
    # Show webcam
    # -----------------------------------
    cv2.imshow(
        "Face Recognition Attendance System",
        frame
    )

    # ESC key to exit
    if cv2.waitKey(1) & 0xFF == 27:
        break

# -----------------------------------
# Cleanup
# -----------------------------------
cap.release()
cv2.destroyAllWindows()