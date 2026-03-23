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
import sys

# ==== CONFIGURAZIONE ====
AUTHORIZED_NAMES = ["andi", "peppe"]   # Nomi autorizzati
GPIO_PIN         = 26
ENCODINGS_FILE   = "encodings.pickle"
GESTURE_DURATION = 5                   # Secondi di finestra gestuale
FACE_COOLDOWN    = 2.0                 # Secondi minimi tra un'attivazione e la successiva
FACE_TOLERANCE   = 0.50               # Soglia distanza face-recognition (più basso = più severo)

# ==== COSTANTI MEDIAPIPE ====
FINGER_TIPS = [4, 8, 12, 16, 20]
FINGER_PIP  = [2, 6, 10, 14, 18]   # PIP per le dita (più affidabile di DIP per le dita chiuse)

# ==== HARDWARE ====
output = LED(GPIO_PIN)

# ==== STATO GLOBALE ====
dj_lock          = threading.Lock()
is_dj_flag       = False
last_activation  = 0.0   # timestamp ultima attivazione (cooldown)

# ==== CARICAMENTO ENCODINGS ====
print("[INFO] Caricamento encodings...")
with open(ENCODINGS_FILE, "rb") as f:
    data = pickle.loads(f.read())
known_face_encodings = data["encodings"]
known_face_names     = data["names"]
print(f"[INFO] {len(known_face_encodings)} encoding/i caricati.")

# ==== CAMERA ====
# Due configurazioni ottimizzate per i rispettivi task:
#   FACE    → alta risoluzione (1920x1080) per dettagli facciali precisi
#   GESTURE → bassa risoluzione (640x480) per alta frequenza e bassa latenza
CONFIG_FACE    = {"format": "XRGB8888", "size": (1920, 1080)}
CONFIG_GESTURE = {"format": "XRGB8888", "size": (640, 480)}

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main=CONFIG_FACE))
picam2.start()
time.sleep(1.5)   # warm-up iniziale

# cv_scaler per face recognition: riduce 1920x1080 → 480x270 prima di elaborare
cv_scaler = 4


def switch_to_gesture():
    """Passa alla configurazione ottimizzata per gesture detection."""
    picam2.stop()
    picam2.configure(picam2.create_preview_configuration(main=CONFIG_GESTURE))
    picam2.start()
    time.sleep(0.3)   # stabilizzazione esposizione


def switch_to_face():
    """Ripristina la configurazione ottimizzata per face recognition."""
    picam2.stop()
    picam2.configure(picam2.create_preview_configuration(main=CONFIG_FACE))
    picam2.start()
    time.sleep(0.3)

# ==== MEDIAPIPE HANDS (istanza unica, non si ri-crea ad ogni chiamata) ====
mp_hands    = mp.solutions.hands
hands_model = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.75,
    min_tracking_confidence=0.75,
)

# ---------------------------------------------------------------------------
# UTILITY
# ---------------------------------------------------------------------------

def fingers_up(hand_landmarks, handedness_label: str) -> list[int]:
    """
    Restituisce lista [pollice, indice, medio, anulare, mignolo] con 1=su, 0=giù.
    Gestisce correttamente mano destra e sinistra per il pollice.
    """
    lm = hand_landmarks.landmark
    status = []

    # --- Pollice: confronto sull'asse X, invertito per mano sinistra ---
    if handedness_label == "Right":
        status.append(1 if lm[FINGER_TIPS[0]].x < lm[FINGER_PIP[0]].x else 0)
    else:
        status.append(1 if lm[FINGER_TIPS[0]].x > lm[FINGER_PIP[0]].x else 0)

    # --- Altre 4 dita: confronto sull'asse Y (tip sopra PIP = dito alzato) ---
    for tip, pip in zip(FINGER_TIPS[1:], FINGER_PIP[1:]):
        status.append(1 if lm[tip].y < lm[pip].y else 0)

    return status


def run_command(scelta: int):
    """Esegue il comando corrispondente al numero di dita rilevato."""
    commands = {
        1: ['amixer', 'sset', 'Master', '25%+'],
        2: ['amixer', 'sset', 'Master', '25%-'],
        4: ['playerctl', 'play'],
        5: ['playerctl', 'pause'],
    }
    if scelta in commands:
        print(f"[CMD] Eseguo comando per {scelta} dita: {' '.join(commands[scelta])}")
        subprocess.Popen(commands[scelta])   # non-bloccante
    else:
        print(f"[CMD] Nessun comando per {scelta} dita.")


# ---------------------------------------------------------------------------
# GESTURE DETECTION
# ---------------------------------------------------------------------------

def print_progress(remaining: float, total: float, fingers: int | None):
    """Stampa una barra di progresso inline nel terminale."""
    filled  = int((1 - remaining / total) * 20)
    bar     = "█" * filled + "░" * (20 - filled)
    f_str   = f"  Dita rilevate: {fingers}" if fingers is not None else "  (nessuna mano)"
    sys.stdout.write(f"\r[{bar}] {remaining:4.1f}s{f_str}   ")
    sys.stdout.flush()


def gesture_detection(duration: float = GESTURE_DURATION):
    """
    Finestra temporale in cui si rileva il gesto (numero di dita alzate).
    Usa la stessa istanza camera già attiva — nessun stop/start.
    Feedback tramite barra di progresso nel terminale (nessun display grafico richiesto).
    """
    print("\n[GESTURE] Cambio configurazione camera → 640x480 bassa latenza...")
    switch_to_gesture()
    print(f"[GESTURE] Mostra la mano! Hai {duration}s per il comando.")
    end_time = time.time() + duration
    campioni = []   # raccoglie il n° di dita ad ogni frame valido

    while time.time() < end_time:
        remaining = end_time - time.time()
        frame     = picam2.capture_array()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)   # XRGB8888 → RGB
        results   = hands_model.process(frame_rgb)

        detected_count = None
        if results.multi_hand_landmarks and results.multi_handedness:
            hand_lm    = results.multi_hand_landmarks[0]   # max_num_hands=1
            handedness = results.multi_handedness[0].classification[0].label
            f_status   = fingers_up(hand_lm, handedness)
            detected_count = sum(f_status)
            campioni.append(detected_count)

        print_progress(remaining, duration, detected_count)
        time.sleep(0.08)   # ~12 fps, più che sufficiente per la gesture

    print()   # va a capo dopo la barra

    if campioni:
        scelta_finale = Counter(campioni).most_common(1)[0][0]
        print(f"[GESTURE] Campioni: {campioni}  →  Scelta finale: {scelta_finale} dita")
        run_command(scelta_finale)
    else:
        print("[GESTURE] Nessuna mano rilevata — nessun comando eseguito.")

    print("[GESTURE] Ripristino configurazione camera → 1920x1080 face recognition...")
    switch_to_face()


# ---------------------------------------------------------------------------
# ACTIVATE DJ
# ---------------------------------------------------------------------------

def activate_dj():
    """
    Accende il LED, avvia la finestra gestuale, spegne il LED.
    Protetto da lock per evitare attivazioni concorrenti.
    """
    global is_dj_flag
    with dj_lock:
        if is_dj_flag:
            return
        is_dj_flag = True
        output.on()
        print("[DJ] LED acceso — finestra comandi attiva.")

    try:
        gesture_detection()
    finally:
        output.off()
        with dj_lock:
            is_dj_flag = False
        print("[DJ] LED spento — sistema in attesa.")


# ---------------------------------------------------------------------------
# FACE RECOGNITION
# ---------------------------------------------------------------------------

def process_frame(frame) -> tuple[str, bool]:
    """
    Ridimensiona il frame, cerca volti e restituisce (nome, autorizzato).
    """
    small  = cv2.resize(frame, (0, 0), fx=1/cv_scaler, fy=1/cv_scaler)
    rgb    = cv2.cvtColor(small, cv2.COLOR_BGRA2RGB)

    locations = face_recognition.face_locations(rgb, model="hog")
    encodings = face_recognition.face_encodings(rgb, locations, num_jitters=1)

    for enc in encodings:
        distances = face_recognition.face_distance(known_face_encodings, enc)
        best_idx  = int(np.argmin(distances))

        if distances[best_idx] <= FACE_TOLERANCE:
            name = known_face_names[best_idx]
            if name in AUTHORIZED_NAMES:
                return name, True

    return "Unknown", False


def face_recognition_loop():
    global last_activation

    print("[INFO] Face recognition avviato. Premi Ctrl+C per uscire.")
    frame_interval = 0.15   # ~6-7 FPS per il loop face-recognition (basta per la rilevazione)

    try:
        while True:
            t0    = time.time()
            frame = picam2.capture_array()

            # Salta il riconoscimento se è già attivo il modo gesti
            if not is_dj_flag:
                name, authorized = process_frame(frame)

                now = time.time()
                if authorized and (now - last_activation) >= FACE_COOLDOWN:
                    last_activation = now
                    print(f"[FACE] Volto autorizzato: {name} — avvio thread DJ.")
                    threading.Thread(target=activate_dj, daemon=True).start()

            # Mantieni il framerate desiderato
            elapsed = time.time() - t0
            sleep_t = max(0.0, frame_interval - elapsed)
            time.sleep(sleep_t)

    except KeyboardInterrupt:
        print("\n[INFO] Interruzione utente.")
    finally:
        picam2.stop()
        output.off()
        hands_model.close()
        print("[INFO] Risorse rilasciate. Uscita.")


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    face_recognition_loop()
