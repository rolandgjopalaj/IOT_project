import face_recognition
import cv2
import numpy as np
from picamera2 import Picamera2
import time
import pickle
from gpiozero import LED
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading
from datetime import datetime

# ==== CONFIGURATION ====
AUTHORIZED_NAMES = ["andi", "peppe"]  # Case-sensitive
GPIO_PIN = 26
HTTP_HOST = ''
HTTP_PORT = 8000
ENCODINGS_FILE = "encodings.pickle"

# ==== GLOBALS ====
output = LED(GPIO_PIN)
door_lock = threading.Lock()
door_open_flag = False  # Shared flag for door state

# ==== read the pass phrase ====
def read_parola_dordine():
    with open("parola", 'r') as file:
        parola = file.read().strip()
        return parola


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

def open_door(duration=5):
    global door_open_flag
    with door_lock:
        if not door_open_flag:
            print("[INFO] Opening door")
            output.on()
            door_open_flag = True
            time.sleep(duration)
            output.off()
            door_open_flag = False
            print("[INFO] Door closed")

def save_log(utente, status):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open('public_web/accessi.txt', 'a') as log_file:
        log_file.write(f"Time: {timestamp} - Utente: {utente} - Status: {status}\n")


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
        if not door_open_flag:
            threading.Thread(target=open_door).start()
            print(f"[INFO] Door triggered by face: {name}")
            # Log the access
            save_log(name, "ENTRATO")

    return name, authorized_face_detected

def face_recognition_loop():
    print("[INFO] Face recognition loop started. Door is initially closed.")
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

# ==== HTTP SERVER SETUP ====
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            try:
                with open('public_web/index.html', 'rb') as file:
                    html_content = file.read()
                self.wfile.write(html_content)
            except Exception:
                self.wfile.write(b"<html><body><h1>Index file not found.</h1></body></html>")
        
        elif self.path == '/accessi':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            try:
                with open('public_web/accessi.html', 'rb') as file:
                    html_content = file.read()
                self.wfile.write(html_content)
            except Exception:
                self.wfile.write(b"<html><body><h1>Accessi file not found.</h1></body></html>")

        else:
            self.send_error(404, "File Not Found: %s" % self.path)

    def do_POST(self):
        status = ""
        if self.path == '/apri':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data_bytes = self.rfile.read(content_length)
                post_data_str = post_data_bytes.decode('utf-8')
                
                data = json.loads(post_data_str)
                utente = data.get("utente")
                parola_dordine = data.get("parola_dordine")
                
                if parola_dordine == read_parola_dordine():
                    # Open the door in a separate thread if not already open
                    if not door_open_flag:
                        threading.Thread(target=open_door).start()
                    status = "ENTRATO"
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b"Accesso Consentito! Corri!!!")
                else:
                    status = "NEGATO"
                    output.off()
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b"Accesso Negato!")

                # Log the access
                save_log(utente, status)

            except Exception as e:
                print(f"Errore durante l'elaborazione della richiesta POST: {e}")
                self.send_error(500, "Errore interno del server")
        
        elif self.path == '/accessi':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data_bytes = self.rfile.read(content_length)
                post_data_str = post_data_bytes.decode('utf-8')
                data = json.loads(post_data_str)
                parola_dordine = data.get("parola_dordine")

                # Cambia la password qui se vuoi
                if parola_dordine == read_parola_dordine():
                    try:
                        with open('public_web/accessi.txt', 'r') as log_file:
                            logs = log_file.read()
                        self.send_response(200)
                        self.send_header('Content-type', 'text/plain')
                        self.end_headers()
                        self.wfile.write(logs.encode())
                    except Exception as e:
                        self.send_response(500)
                        self.send_header('Content-type', 'text/plain')
                        self.end_headers()
                        self.wfile.write(f"Errore lettura log: {e}".encode())
                else:
                    self.send_response(403)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b"Password errata!")
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(f"Errore nella richiesta: {e}".encode())
        
        else:
            self.send_error(404, "Endpoint Not Found: %s" % self.path)


        

def run_http_server():
    server_address = (HTTP_HOST, HTTP_PORT)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f"[INFO] HTTP server running at http://localhost:{HTTP_PORT} ...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] HTTP server stopped.")
        httpd.server_close()

# ==== MAIN ====
if __name__ == '__main__':
    # Start face recognition in a thread
    face_thread = threading.Thread(target=face_recognition_loop, daemon=True)
    face_thread.start()
    # Start HTTP server in main thread
    run_http_server()
    # On exit
    output.off()
