import face_recognition
import cv2
import numpy as np
from picamera2 import Picamera2
import time
import pickle
from gpiozero import LED
import threading
import mediapipe as mp
from collections import Counter
import subprocess

# ==== CONFIGURAZIONE ====
AUTHORIZED_NAMES = ["andi", "peppe"]  # Modifica con i nomi autorizzati
GPIO_PIN = 26
ENCODINGS_FILE = "encodings.pickle"

# ==== GLOBALI ====
output = LED(GPIO_PIN)
dj_lock = threading.Lock()
is_dj_flag = False  # Indica presenza DJ

# ==== FACE RECOGNITION SETUP ====
print("[INFO] Caricamento encodings...")
with open(ENCODINGS_FILE, "rb") as f:
    data = pickle.loads(f.read())
known_face_encodings = data["encodings"]
known_face_names = data["names"]

#avvia la webcam con la configurazione giusta
#in questo caso si configura per il riconoscimento facciale
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (1920, 1080)}))
picam2.start()
cv_scaler = 4

#funzione che calcola le frequenze assolute
#restituisce il valore con la frequenza maggiore
def frequenzaAssolutaPiuAlta(dati):
    if not dati:
        return 0
    else:
        return Counter(dati).most_common(1)[0][0] # Restituisce il valore più comune

#avvia il comando desiderato in base alla scelta
def gestioneDellaScelta(sceltaFinale):
    match sceltaFinale:
        case 1:
            subprocess.run(['amixer', 'sset', 'Master', '25%+'])
        case 2:
            subprocess.run(['amixer', 'sset', 'Master', '25%-'])
        case 3:
            print("c")
        case 4:
            subprocess.run(['playerctl', 'play'])
        case 5:
            subprocess.run(['playerctl', 'pause'])
        case _:
            print("Nessun comando!")


      
#la funzione per rilevare e riconoscere i gesti con la mano
def gesture_detection(duration=5):
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1,
                           min_detection_confidence=0.7, min_tracking_confidence=0.7)

    picam2.stop()
    #configura la webcam per il riconoscimento dei gesti (mano)
    picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
    picam2.start()

    FINGER_TIPS = [4, 8, 12, 16, 20]
    FINGER_DIP = [3, 7, 11, 15, 19]

    #cerca di capire quante dita sono su
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

    #cerca di capira la scelta del utente 
    #quante dita ha tenuto su per piu tempo
    try:
        #per evitare gli errori calcoliamo la scelta con la frequenza maggiore
        scelte = []
        
        while time.time() < end_time:
            frame = picam2.capture_array()
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)
        
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    #calcola quante dita sono su
                    fingerPositions = fingers_up(hand_landmarks)
                    contaggiDitaSu = sum(fingerPositions)
                    print(contaggiDitaSu)
                    scelte.append(contaggiDitaSu)
                    
            time.sleep(0.1)
        
        print(f"Le scelte: {scelte}")
        sceltaFinale = frequenzaAssolutaPiuAlta(scelte)
        print(f"Scelta finale: {sceltaFinale}")
        gestioneDellaScelta(sceltaFinale)

    except KeyboardInterrupt:
        pass

    picam2.stop()
    #reimposta la configurazione per il riconoscimento facciale
    picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (1920, 1080)}))
    picam2.start()
    hands.close()
    print("[INFO] gesture detection terminato")

#attiva la possibilita di usare "hand gestures"
def activate_dj(duration=5):
    global is_dj_flag
    with dj_lock:
        if not is_dj_flag:
            print("[INFO] DJ riconosciuto")
            output.on()
            is_dj_flag = True
            gesture_detection(duration=duration)
            output.off()
            is_dj_flag = False
            print("[INFO] DJ time out")

#la funzione per rilevare e riconoscere i volti
def process_frame(frame):
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

    if authorized_face_detected and not is_dj_flag:
        threading.Thread(target=activate_dj).start()
        print(f"[INFO] DJ trovato, face: {name}")

    return name, authorized_face_detected


def face_recognition_loop():
    print("[INFO] Face recognition loop started.")
    try:
        while True:
            frame = picam2.capture_array()
            name, detected = process_frame(frame)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("[INFO] Face recognition stopped.")
    finally:
        picam2.stop()
        output.off()

if __name__ == '__main__':
    face_recognition_loop()
    output.off()
