from picamera2 import Picamera2
import time
import mediapipe as mp
import cv2

# Setup MediaPipe hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False,
                       max_num_hands=2,
                       min_detection_confidence=0.7,
                       min_tracking_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# Setup Picamera2
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()

# Definizione dita
FINGER_TIPS = [4, 8, 12, 16, 20]
FINGER_DIP = [3, 7, 11, 15, 19]

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

try:
    while True:
        frame = picam2.capture_array()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        total_fingers_up = []

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                total_fingers_up = fingers_up(hand_landmarks)

        print(f"Dita alzate: {total_fingers_up}")
        time.sleep(0.1)  # per ridurre l'uso della CPU

except KeyboardInterrupt:
    pass

picam2.stop()
hands.close()
