# Setup Ambiente

## Installazione iniziale

Esegui questi comandi **una sola volta** per configurare l'ambiente:

```bash
python3 -m venv --system-site-packages face_rec
source face_rec/bin/activate
sudo apt update && sudo apt full-upgrade
pip install opencv-python imutils face-recognition mediapipe
sudo apt install cmake
```

## Ogni volta che riapri il terminale

Esegui questo comando per attivare l'ambiente e spostarti nella cartella del progetto:

```bash
cd && source face_rec/bin/activate && cd YourProjectFolder/
```

> **Nota:** Sostituisci `YourProjectFolder/` con il nome della tua cartella di progetto.
