# MagicHands

Il sistema rileva la presenza di un volto tramite la webcam e utilizza modelli di intelligenza artificiale per verificarne l'identità confrontandola con una lista di utenti autorizzati. In caso di riconoscimento positivo, un LED verde si accende per segnalare l'accesso consentito e dare inizio a una finestra temporale di 5 secondi durante la quale l'utente può impartire comandi gestuali rapidi.

Durante questo intervallo, la videocamera analizza la mano dell'utente e il numero di dita visibili (alzate) per interpretare azioni predefinite:

| Dita | Azione |
|------|--------|
| 5 dita | Interrompe la musica |
| 4 dita | Avvia la musica |
| 2 dita | Riduce il volume del 25% |
| 1 dito | Aumenta il volume del 25% |

Trascorsi i 5 secondi, il LED verde si spegne automaticamente e il sistema torna in modalità di attesa, pronto a rilevare nuovamente un volto autorizzato per consentire ulteriori comandi.

---

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
