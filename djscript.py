import face_recognition
import cv2
import numpy as np
from picamera2 import Picamera2
import time
import pickle
from gpiozero import LED
import threading

# ==== CONFIGURATION ====
AUTHORIZED_NAMES = ["andi", "peppe"]  # Case-sensitive
GPIO_PIN = 26
ENCODINGS_FILE = "encodings.pickle"

# ==== GLOBALS ====
output = LED(GPIO_PIN)
dj_lock = threading.Lock()
is_dj_flag = False  # Shared flag for door state

# ==== FACE RECOGNITION SETUP ====
print("[INFO] loading encodings...")
with open(ENCODINGS_FILE, "rb") as f:
    data = pickle.loads(f.read())
known_face_encodings = data["encodings"]
known_face_names = data["names"]

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (1920, 1080)}))
picam2.start()
cv_scaler = 4

def activate_dj(duration=10):
    global is_dj_flag
    with dj_lock:
        if not is_dj_flag:
            print("[INFO] DJ recognized")
            output.on()
            is_dj_flag = True
            time.sleep(duration)
            output.off()
            is_dj_flag = False
            print("[INFO] DJ time out")

def process_frame(frame):
    # Resize and convert frame for face recognition
    resized_frame = cv2.resize(frame, (0, 0), fx=(1/cv_scaler), fy=(1/cv_scaler))
    rgb_resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_resized_frame)
    face_encodings = face_recognition.face_encodings(rgb_resized_frame, face_locations, model='large')
    authorized_face_detected = False
    name = "Unknown"
    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            name = known_face_names[best_match_index]
            if name in AUTHORIZED_NAMES:
                authorized_face_detected = True
                break
    if authorized_face_detected:
        # Open the door in a separate thread if not already open
        if not is_dj_flag:
            threading.Thread(target=activate_dj).start()
            print(f"[INFO] DJ found, face: {name}")
    return name, authorized_face_detected

def face_recognition_loop():
    print("[INFO] Face recognition loop started.")
    try:
        while True:
            frame = picam2.capture_array()
            name, detected = process_frame(frame)
            # Optionally, add a small sleep to reduce CPU usage
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("[INFO] Face recognition stopped.")
    finally:
        picam2.stop()
        output.off()

# ==== MAIN ====
if __name__ == '__main__':
    # Start face recognition loop (no logging, no web server)
    face_recognition_loop()
    # On exit
    output.off()
