import cv2
import time

# Load the face detection model
face_cascade = cv2.CascadeClassifier("data/haarcascade_frontalface_default.xml")

cap = cv2.VideoCapture(0)
prev_time = 0

while True:
    ret, frame = cap.read()

    if not ret:
        print("Failed to access camera")
        break
    
    current_time = time.time()
    fps = 1 / (current_time - prev_time) if prev_time != 0 else 0
    prev_time = current_time
    
    # Convert to grayscale (important for detection)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    face_count = len(faces)

    cv2.putText(frame, f"FPS: {int(fps)}", (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # Draw rectangle around faces
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

    cv2.imshow("Face Detection", frame)

    cv2.putText(frame, f"Faces B: {face_count}", (10, 30),

            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()