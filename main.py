import cv2
import face_recognition
import os
import time

# Load known faces
known_encodings = []
known_names = []

for file in os.listdir("known_faces"):
    img = face_recognition.load_image_file(f"known_faces/{file}")
    encodings = face_recognition.face_encodings(img)

if len(encodings) > 0:
    known_encodings.append(encodings[0])
    known_names.append(file.split(".")[0])
else:
    print(f"No face found in {file}")
    known_encodings.append(encoding)
    known_names.append(file.split(".")[0])

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    faces = face_recognition.face_locations(rgb)
    encodings = face_recognition.face_encodings(rgb, faces)

    for (top, right, bottom, left), face_encoding in zip(faces, encodings):

        matches = face_recognition.compare_faces(known_encodings, face_encoding)
        name = "Unknown"

        if True in matches:
            index = matches.index(True)
            name = known_names[index]

        cv2.rectangle(frame, (left, top), (right, bottom), (0,255,0), 2)
        cv2.putText(frame, name, (left, top-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

    cv2.imshow("Recognition", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()