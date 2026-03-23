import face_recognition
import cv2
import numpy as np
from picamera2 import Picamera2
import time
import pickle
from gpiozero import LED
import mediapipe as mp
from collections import Counter
import subprocess

# ==== CONFIGURAZIONE ====
AUTHORIZED_NAMES = ["andi", "peppe"]
GPIO_PIN = 26
ENCODINGS_FILE = "encodings.pickle"

# ==== SETUP ====
output = LED(GPIO_PIN)

print("[INFO] Caricamento encodings...")
with open(ENCODINGS_FILE, "rb") as f:
    data = pickle.loads(f.read())
known_face_encodings = data["encodings"]
known_face_names = data["names"]

picam2 = Picamera2()
cv_scaler = 4

def frequenzaAssolutaPiuAlta(dati):
    if not dati:
        return 0
    return Counter(dati).most_common(1)[0][0]

def gestioneDellaScelta(sceltaFinale):
    match sceltaFinale:
        case 1:
            subprocess.run(['amixer', 'sset', 'Master', '25%+'])
        case 2:
            subprocess.run(['amixer', 'sset', 'Master', '25%-'])
        case 4:
            subprocess.run(['playerctl', 'play'])
        case 5:
            subprocess.run(['playerctl', 'pause'])
        case _:
            print("Nessun comando!")

def gesture_detection(duration=5):
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1,
                           min_detection_confidence=0.7, min_tracking_confidence=0.7)

    picam2.stop()
    picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
    picam2.start()

    FINGER_TIPS = [4, 8, 12, 16, 20]
    FINGER_DIP  = [3, 7, 11, 15, 19]

    def fingers_up(hand_landmarks):
        fingers_status = []
        if hand_landmarks.landmark[FINGER_TIPS[0]].x > hand_landmarks.landmark[FINGER_DIP[0]].x:
            fingers_status.append(1)
        else:
            fingers_status.append(0)
        for tip, dip in zip(FINGER_TIPS[1:], FINGER_DIP[1:]):
            if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[dip].y:
                fingers_status.append(1)
            else:
                fingers_status.append(0)
        return fingers_status

    print("[INFO] Avvio gesture detection per 5 secondi")
    end_time = time.time() + duration
    scelte = []

    while time.time() < end_time:
        frame = picam2.capture_array()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                contaggiDitaSu = sum(fingers_up(hand_landmarks))
                print(contaggiDitaSu)
                scelte.append(contaggiDitaSu)

        time.sleep(0.1)

    sceltaFinale = frequenzaAssolutaPiuAlta(scelte)
    print(f"Scelta finale: {sceltaFinale}")
    gestioneDellaScelta(sceltaFinale)

    hands.close()
    picam2.stop()
    picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (1920, 1080)}))
    picam2.start()
    print("[INFO] Gesture detection terminata")

def process_frame(frame):
    resized_frame = cv2.resize(frame, (0, 0), fx=(1/cv_scaler), fy=(1/cv_scaler))
    rgb_resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_resized_frame)
    face_encodings = face_recognition.face_encodings(rgb_resized_frame, face_locations, model='large')

    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            name = known_face_names[best_match_index]
            if name in AUTHORIZED_NAMES:
                return name, True

    return "Unknown", False

def face_recognition_loop():
    picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (1920, 1080)}))
    picam2.start()
    print("[INFO] Face recognition loop avviato.")

    try:
        while True:
            frame = picam2.capture_array()
            name, detected = process_frame(frame)

            if detected:
                print(f"[INFO] Utente autorizzato rilevato: {name}")
                output.on()
                gesture_detection(duration=5)
                output.off()
                print("[INFO] Pronto per il prossimo riconoscimento")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("[INFO] Fermato.")
    finally:
        picam2.stop()
        output.off()

if __name__ == '__main__':
    face_recognition_loop()
