import cv2
import os
from datetime import datetime
from picamera2 import Picamera2
import time 

# Crea una cartella dentro il "dataset" con il nome dato dall'utente.
def create_folder(name):
    dataset_folder = "dataset"
    if not os.path.exists(dataset_folder):
        os.makedirs(dataset_folder)
    
    person_folder = os.path.join(dataset_folder, name)
    if not os.path.exists(person_folder):
        os.makedirs(person_folder)
    return person_folder

def capture_photos(name):
    folder = create_folder(name)
    
    # Inizializza la telecamera 
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
    picam2.start()

    # Serve per dare tempo alla telecamera a "scaldarsi"
    time.sleep(2)

    photo_count = 0
    
    print(f"Taking photos for {name}. Press SPACE to capture, 'q' to quit.")
    
    while True:
        # Acquisisce un'immagine dalla camera Pi e la memorizza nella variabile
        frame = picam2.capture_array()
        
        # Mostra il frame acquisito in una finestra chiamata 'Capture'
        cv2.imshow('Capture', frame)
        
        # Attende per 1 millisecondo la pressione di un tasto e salva il codice del tasto premuto
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(' '):  # Space key: Se premuto fa il seguente
            photo_count += 1 # Contatore per il nr delle foto
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") # Crea una stringa con la data e ora corrente (per evitare conflitti di nome nei file
            filename = f"{name}_{timestamp}.jpg" # Crea il nome del file(foto) prima di salvarla
            filepath = os.path.join(folder, filename) # Ottiene il percorso completo del file all’interno della cartella specificata.
            cv2.imwrite(filepath, frame) # Salva il frame corrente come immagine JPEG nel percorso appena generato.

            print(f"Photo {photo_count} saved: {filepath}")
        
        elif key == ord('q'):  # Q key: Se premuto rompe il ciclo
            break
    
    # Rilascia e chiude tutto prima di terminare
    cv2.destroyAllWindows()
    picam2.stop()
    
    print(f"Photo capture completed. {photo_count} photos saved for {name}.")

if __name__ == "__main__":
    name = input("Inserisci un nome: ")
    capture_photos(name)