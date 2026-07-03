from flask import Flask, render_template, request, redirect, url_for, session, Response
from werkzeug.security import generate_password_hash, check_password_hash

import sqlite3
import os
from datetime import datetime

import cv2
import face_recognition
import numpy as np
import time

app = Flask(__name__)

# -----------------------------------
# Secret Key
# -----------------------------------
app.secret_key = "mysecretkey"

# -----------------------------------
# Known Faces
# -----------------------------------
known_encodings = []
known_names = []

KNOWN_FACES_DIR = "known_faces"

# -----------------------------------
# Load Faces Function
# -----------------------------------
def load_known_faces():

    global known_encodings
    global known_names

    known_encodings.clear()
    known_names.clear()

    for file in os.listdir(KNOWN_FACES_DIR):

        path = os.path.join(
            KNOWN_FACES_DIR,
            file
        )

        img = face_recognition.load_image_file(
            path
        )

        encodings = face_recognition.face_encodings(
            img
        )

        if len(encodings) > 0:

            known_encodings.append(
                encodings[0]
            )

            known_names.append(
                os.path.splitext(file)[0]
            )

            print(f"Loaded: {file}")

        else:

            print(
                f"[ERROR] No detectable face in: {file}"
            )

# Initial Face Load
load_known_faces()

# -----------------------------------
# Webcam
# -----------------------------------
camera = cv2.VideoCapture(0)

# -----------------------------------
# Video Streaming Function
# -----------------------------------
def generate_frames():

    process_this_frame = True

    prev_time = 0

    while True:

        success, frame = camera.read()

        if not success:
            break

        # Resize for performance
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

        if process_this_frame:

            face_locations = face_recognition.face_locations(
                rgb_small
            )

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

                    best_match_index = np.argmin(
                        distances
                    )

                    if distances[best_match_index] < 0.6:

                        name = known_names[
                            best_match_index
                        ]

                        # -----------------------------------
                        # Attendance Logic
                        # -----------------------------------
                        conn = sqlite3.connect(
                            "users.db"
                        )

                        cursor = conn.cursor()

                        # Get active session
                        cursor.execute(
                            """
                            SELECT subject,
                                   start_time,
                                   end_time

                            FROM active_session
                            LIMIT 1
                            """
                        )

                        active_session = cursor.fetchone()

                        if active_session:

                            subject = active_session[0]
                            start_time = active_session[1]
                            end_time = active_session[2]

                            current_time_obj = datetime.now().time()

                            start_obj = datetime.strptime(
                                start_time,
                                "%H:%M"
                            ).time()

                            end_obj = datetime.strptime(
                                end_time,
                                "%H:%M"
                            ).time()

                            # Check valid session timing
                            if start_obj <= current_time_obj <= end_obj:

                                now = datetime.now()

                                current_date = now.strftime(
                                    "%Y-%m-%d"
                                )

                                current_time = now.strftime(
                                    "%H:%M:%S"
                                )

                                # -----------------------------------
                                # Prevent Duplicate Attendance
                                # -----------------------------------
                                cursor.execute(
                                    """
                                    SELECT *
                                    FROM attendance

                                    WHERE username=?
                                    AND subject=?
                                    AND date=?
                                    """,
                                    (
                                        name,
                                        subject,
                                        current_date
                                    )
                                )

                                already_marked = cursor.fetchone()

                                if not already_marked:

                                    cursor.execute(
                                        """
                                        INSERT INTO attendance
                                        (
                                            username,
                                            subject,
                                            date,
                                            time
                                        )

                                        VALUES (?, ?, ?, ?)
                                        """,
                                        (
                                            name,
                                            subject,
                                            current_date,
                                            current_time
                                        )
                                    )

                                    conn.commit()

                                    print(
                                        f"{name} attendance marked for {subject}"
                                    )

                                else:

                                    print(
                                        f"{name} already marked for {subject}"
                                    )

                            else:

                                print(
                                    "Attendance session inactive"
                                )

                        conn.close()

                face_names.append(name)

        process_this_frame = not process_this_frame

        # -----------------------------------
        # Draw Results
        # -----------------------------------
        for (top, right, bottom, left), name in zip(
            face_locations,
            face_names
        ):

            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            cv2.rectangle(
                frame,
                (left, top),
                (right, bottom),
                (0, 255, 0),
                2
            )

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
        # FPS Counter
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

        # Convert frame to jpg
        ret, buffer = cv2.imencode(
            ".jpg",
            frame
        )

        frame = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n'
            + frame +
            b'\r\n'
        )

# -----------------------------------
# Register Route
# -----------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    error = ""

    if request.method == "POST":

        username = request.form["username"]

        password = generate_password_hash(
            request.form["password"]
        )

        role = request.form["role"]

        try:

            conn = sqlite3.connect(
                "users.db"
            )

            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO users
                (username, password, role)

                VALUES (?, ?, ?)
                """,
                (
                    username,
                    password,
                    role
                )
            )

            conn.commit()

            conn.close()

            return redirect(
                url_for("login")
            )

        except sqlite3.IntegrityError:

            error = "Username already exists"

    return render_template(
        "register.html",
        error=error
    )

# -----------------------------------
# Login Route
# -----------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():

    error = ""

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        conn = sqlite3.connect(
            "users.db"
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM users
            WHERE username=?
            """,
            (username,)
        )

        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(
            user[2],
            password
        ):

            session["user"] = user[1]

            session["role"] = user[3]

            return redirect(
                url_for("dashboard")
            )

        else:

            error = "Invalid username or password"

    return render_template(
        "login.html",
        error=error
    )

# -----------------------------------
# Upload Face Route
# -----------------------------------
@app.route("/upload", methods=["GET", "POST"])
def upload():

    if "user" not in session:
        return redirect(
            url_for("login")
        )

    if session["role"] != "admin":
        return "Access Denied"

    message = ""

    if request.method == "POST":

        username = request.form["username"]

        image = request.files["image"]

        if image:

            filename = f"{username}.jpg"

            save_path = os.path.join(
                "known_faces",
                filename
            )

            image.save(save_path)

            # Reload faces immediately
            load_known_faces()

            message = "Face uploaded successfully"

    return render_template(
        "upload.html",
        message=message
    )

# -----------------------------------
# Create Attendance Session
# -----------------------------------
@app.route("/session", methods=["GET", "POST"])
def session_page():

    if "user" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return "Access Denied"

    message = ""

    if request.method == "POST":

        subject = request.form["subject"]

        start_time = request.form["start_time"]

        end_time = request.form["end_time"]

        conn = sqlite3.connect("users.db")

        cursor = conn.cursor()

        # Remove old session
        cursor.execute(
            "DELETE FROM active_session"
        )

        # Insert new session
        cursor.execute(
            """
            INSERT INTO active_session
            (subject, start_time, end_time)

            VALUES (?, ?, ?)
            """,
            (
                subject,
                start_time,
                end_time
            )
        )

        conn.commit()

        conn.close()

        message = "Session started successfully"

    return render_template(
        "session.html",
        message=message
    )

# -----------------------------------
# Dashboard Route
# -----------------------------------
@app.route("/")
def dashboard():

    if "user" not in session:

        return redirect(
            url_for("login")
        )

    conn = sqlite3.connect(
        "users.db"
    )

    cursor = conn.cursor()

    # Attendance Data
    if session["role"] == "admin":

        cursor.execute(
            """
            SELECT username,
                   subject,
                   date,
                   time

            FROM attendance

            ORDER BY id DESC
            """
        )

    else:

        cursor.execute(
            """
            SELECT username,
                   subject,
                   date,
                   time

            FROM attendance

            WHERE username=?

            ORDER BY id DESC
            """,
            (session["user"],)
        )

    attendance_data = cursor.fetchall()

    # -----------------------------------
    # Analytics
    # -----------------------------------

    # Total students
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE role='student'
        """
    )

    total_students = cursor.fetchone()[0]

    # Today's attendance
    today_date = datetime.now().strftime(
        "%Y-%m-%d"
    )

    cursor.execute(
        """
        SELECT COUNT(DISTINCT username)
        FROM attendance
        WHERE date=?
        """,
        (today_date,)
    )

    today_attendance = cursor.fetchone()[0]

    # Attendance Percentage
    attendance_percentage = 0

    if total_students > 0:

        attendance_percentage = round(
            (
                today_attendance /
                total_students
            ) * 100,
            2
        )

    # -----------------------------------
    # Active Session
    # -----------------------------------
    cursor.execute(
        """
        SELECT subject,
               start_time,
               end_time

        FROM active_session

        LIMIT 1
        """
    )

    active_session = cursor.fetchone()

    conn.close()

    return render_template(
        "index.html",

        attendance=attendance_data,

        username=session["user"],

        role=session["role"],

        active_session=active_session,

        total_students=total_students,

        today_attendance=today_attendance,

        attendance_percentage=attendance_percentage
    )

# -----------------------------------
# Video Feed Route
# -----------------------------------
@app.route("/video_feed")
def video_feed():

    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# -----------------------------------
# Logout Route
# -----------------------------------
@app.route("/logout")
def logout():

    session.pop("user", None)

    session.pop("role", None)

    return redirect(
        url_for("login")
    )

# -----------------------------------
# Run Flask App
# -----------------------------------
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )