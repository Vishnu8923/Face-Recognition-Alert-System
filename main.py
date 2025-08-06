import cv2
import face_recognition
import os
import numpy as np
from datetime import datetime
import csv

# -------------------------------
# Step 1: Load known face images
# -------------------------------
known_faces_dir = 'known_faces'
known_encodings = []
known_names = []

print("[INFO] Loading known faces...")
for filename in os.listdir(known_faces_dir):
    if filename.endswith('.jpg') or filename.endswith('.png'):
        img_path = os.path.join(known_faces_dir, filename)
        image = face_recognition.load_image_file(img_path)
        encoding = face_recognition.face_encodings(image)
        if encoding:  # check if at least one face was found
            known_encodings.append(encoding[0])
            # filename before extension becomes the name
            known_names.append(os.path.splitext(filename)[0])
        else:
            print(f"[WARNING] No face found in {filename}")

print(f"[INFO] Loaded {len(known_encodings)} known faces.")

# -------------------------------
# Step 2: Setup output filenames
# -------------------------------
today_str = datetime.now().strftime('%Y-%m-%d')
attendance_file = f'output/attendance_{today_str}.csv'
video_file = f'output/recorded_{today_str}.avi'

# -------------------------------
# Step 3: Initialize attendance list
# -------------------------------
attendance_marked = set()  # keep track so each person is marked only once

# -------------------------------
# Step 4: Start webcam & video writer
# -------------------------------
cap = cv2.VideoCapture(0)  # 0 = default camera

# Get video properties to set video writer
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter(video_file, fourcc, 20.0, (frame_width, frame_height))

print("[INFO] Starting camera. Press 'q' to quit.")

# Create/open CSV and write header
with open(attendance_file, mode='w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['Name', 'Timestamp'])

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to grab frame")
            break

        # Resize frame to speed up processing (optional)
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]  # BGR to RGB

        # Detect faces & encode
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        # Compare each face with known faces
        for face_encoding, face_location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
            face_distances = face_recognition.face_distance(known_encodings, face_encoding)
            name = "Unknown"

            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_names[best_match_index]

            # Mark attendance only once per session
            if name != "Unknown" and name not in attendance_marked:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                csvwriter.writerow([name, timestamp])
                attendance_marked.add(name)
                print(f"[INFO] Marked attendance for: {name}")

            # Draw rectangle & name on frame
            top, right, bottom, left = [v*4 for v in face_location]  # scale back up
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 255, 0), 2)

        # Show video
        cv2.imshow('Attendance System', frame)

        # Write the frame into video file
        out.write(frame)

        # Quit when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("[INFO] Exiting...")
            break

# -------------------------------
# Step 5: Cleanup
# -------------------------------
cap.release()
out.release()
cv2.destroyAllWindows()
print(f"[INFO] Attendance saved to {attendance_file}")
print(f"[INFO] Video saved to {video_file}")
