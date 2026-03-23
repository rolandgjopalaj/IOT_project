Setup ambiente: 
    python3 -m venv --system-site-packages face_rec 
    source face_rec/bin/activate 
    sudo apt update && sudo apt full-upgrade 
    pip install opencv-python imutils face-recognition mediapipe 
    sudo apt install cmake

Ogni volta che riapri il terminale: 
    cd && source face_rec/bin/activate && cd YourProjectFolder/
