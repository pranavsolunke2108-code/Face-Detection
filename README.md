# Vision Attendance System

A webcam-based attendance system that recognizes enrolled faces and records attendance during an active, subject-specific session.

The project includes a Flask web application with role-based access and a standalone OpenCV script for simple CSV attendance logging.

## Features

- Real-time webcam face recognition using `face_recognition` and OpenCV
- Admin and student registration and login
- Admin-only face enrollment from the web interface
- Subject attendance sessions with start and end times
- Attendance recorded once per person, subject, and date
- SQLite-backed users, sessions, and attendance records
- Dashboard with attendance records and daily summary statistics
- Standalone mode that writes recognized attendance to a dated CSV file

## Project Structure

```text
app.py                 Flask web application and live video feed
database.py            Creates the SQLite tables
main.py                Standalone webcam attendance script
templates/             Flask HTML templates
known_faces/           Enrolled face images (filename becomes the person's name)
data/                  Haar cascade data file
attendance/            CSV files created by the standalone mode
users.db               SQLite database used by the web application
```

## Requirements

- Python 3
- A webcam
- Python packages: `Flask`, `Werkzeug`, `opencv-python`, `face_recognition`, and `numpy`

Install the packages:

```bash
pip install Flask Werkzeug opencv-python face_recognition numpy
```

> `face_recognition` depends on dlib, which may require platform-specific build tools. Follow the package's installation guidance if the install fails.

## Run the Web Application

1. Initialize the database:

   ```bash
   python database.py
   ```

2. Start the application:

   ```bash
   python app.py
   ```

3. Open `http://localhost:5000` in your browser.

4. Register an account. Admin users can:
   - upload an enrolled face image from the **Upload Face** page;
   - start a subject session with a start and end time; and
   - view all recorded attendance.

   Student users can sign in and view their own attendance records.

Keep enrolled images in `known_faces/`; the filename (without its extension) is used as the recognized name.

## Run the Standalone CSV Mode

For a minimal webcam workflow that records each recognized person once per day:

```bash
python main.py
```

Press <kbd>Esc</kbd> to stop. Records are written to `attendance/YYYY-MM-DD.csv`.

## How Attendance Is Recorded

When the live camera recognizes an enrolled face, the web application records attendance only when an active session exists and the current time falls within that session's configured time window. It prevents another record for the same person, subject, and date.

## Notes

- Recognition quality depends on clear, well-lit enrollment images and webcam conditions.
- This is a project implementation and should be hardened before production use. In particular, configure the Flask secret key securely and protect biometric images and attendance data.
