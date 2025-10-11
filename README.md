# **MagicHands**

Il sistema rileva la presenza di un volto tramite la webcam e utilizza modelli di **intelligenza artificiale** per verificarne l’identità confrontandola con una lista di utenti autorizzati. In caso di riconoscimento positivo, un LED verde si accende per segnalare l’accesso consentito e dare inizio a una finestra temporale di 5 secondi durante la quale l’utente può impartire **comandi gestuali rapidi**.

Durante questo intervallo, la videocamera analizza la mano dell’utente e il numero di dita visibili (alzate) per interpretare azioni predefinite, come:

- **5 dita:** interrompe la musica
- **4 dita:** avvia la musica
- **2 dita:** riduce il volume del 25%
- **1 dito:** aumenta il volume del 25%

Trascorsi i 5 secondi, il LED verde si spegne automaticamente e il sistema torna in modalità di attesa, pronto a rilevare nuovamente un volto autorizzato per consentire ulteriori comandi.

# Requisiti

Hardware:

- Raspberry pi 4b (con Micro SD Card ≥ 32GB)
- Pi Camera (qualsiasi telecamera supportata da raspberry pi)
- Led semplice (con resistenza se necessario)

Software:

- Raspberry PI OS
- Python3 (ultima versione stabile)

# Installazione e settaggio

### Dispositivo:

Assemblare il raspberry pi connettendo la telecamera e il led. Nel nostro caso il led e stato collegato usando “GPIO_PIN = 26”. Successivamente bisogna installare Pi OS nella Micro SD Card.  Ciò si può fare usando [Raspberry Pi Imager](https://www.raspberrypi.com/software/).  Una volta installato l’OS, inserire la SD Card, accendere e configurare il raspberry pi ([Tutorial ufficiale](https://www.raspberrypi.com/documentation/computers/getting-started.html)). 

*Suggerimento*: Aggiornare tutti i pacchetti del sistema. Eseguire nel terminale i seguenti comandi: “***sudo apt update”*** e ***“sudo apt full-upgrade”.***

### Progetto:

Per questo progetto dobbiamo settare e usare un ambiente virtuale (Virtual Environment: spazi virtuali e isolati che permettono lo sviluppo e l’esecuzione di progetti/programmi senza il rischio di fare danni al sistema). Il nome del nostro spazio virtuale sara “face_rec”
Istruzioni: (terminale)

- creazione: ***python3 -m venv --system-site-packages face_rec***
- attivazione: ***source face_rec/bin/activate***

Successivamente bisogna spostarsi nella cartella del progetto ”***cd percorso/del/progetto***” (prima crea la cartella). Ora che abbiamo creato e attivato l’ambiente virtuale e ci troviamo nella cartella del progetto dobbiamo installare tutte le dipendenze necessarie. 
(Terminale):

- ***pip install opencv-python***
- ***pip install imutils***
- ***sudo apt install cmake***
- ***pip install face-recognition***
- ***pip install mediapipe***
