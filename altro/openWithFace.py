import face_recognition
import cv2
import numpy as np
from picamera2 import Picamera2
import time
import pickle
from gpiozero import LED



# Load pre-trained face encodings
print("[INFO] loading encodings...")
with open("encodings.pickle", "rb") as f:
    data = pickle.loads(f.read())
known_face_encodings = data["encodings"]
known_face_names = data["names"]

# Initialize the camera
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (1920, 1080)}))
picam2.start()

# Initialize GPIO
output = LED(19)

# Initialize our variables
cv_scaler = 4 # this has to be a whole number

face_locations = []
face_encodings = []
face_names = []
frame_count = 0
start_time = time.time()
fps = 0

# List of names that will trigger the GPIO pin
authorized_names = ["andi", "K_nex"]  # Replace with names you wish to authorise THIS IS CASE-SENSITIVE

flag_passando = False

def process_frame(frame):    
    global face_locations, face_encodings, face_names, flag_passando
    
    # Resize the frame using cv_scaler to increase performance (less pixels processed, less time spent)
    resized_frame = cv2.resize(frame, (0, 0), fx=(1/cv_scaler), fy=(1/cv_scaler))
    
    # Convert the image from BGR to RGB colour space, the facial recognition library uses RGB, OpenCV uses BGR
    rgb_resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
    
    # Find all the faces and face encodings in the current frame of video
    face_locations = face_recognition.face_locations(rgb_resized_frame)
    face_encodings = face_recognition.face_encodings(rgb_resized_frame, face_locations, model='large')
    
    face_names = []
    authorized_face_detected = False
    
    for face_encoding in face_encodings:
        # See if the face is a match for the known face(s)
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"
        
        # Use the known face with the smallest distance to the new face
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            name = known_face_names[best_match_index]
            # Check if the detected face is in our authorized list
            if name in authorized_names:
                authorized_face_detected = True
        face_names.append(name)
    
    # Control the GPIO pin based on face detection
    if authorized_face_detected:
        output.on()  # Turn on Pin
        if not flag_passando:
            print("apperto "+name)
            flag_passando = True
        
    else:
        output.off()  # Turn off Pin
        if flag_passando:
            print("chiuso")
            flag_passando = False
        
    return frame


print("chiuso")
while True:

    # Capture a frame from camera
    frame = picam2.capture_array()
    
    # Process the frame with the function
    processed_frame = process_frame(frame)
    

# By breaking the loop we run this code here which closes everything
picam2.stop()
output.off()  # Make sure to turn off the GPIO pin when exiting
