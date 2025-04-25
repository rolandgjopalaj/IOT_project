# IOT_project
# Sistema di Riconoscimento Facciale e Controllo Accessi con Raspberry Pi

Questo progetto implementa un sistema di controllo accessi basato su riconoscimento facciale e interfaccia HTTP, utilizzando Raspberry Pi, PiCamera2, GPIO e un semplice web server Python.

---

## Indice

- [Requisiti](#requisiti)
- [Funzionalità](#funzionalità)
- [Struttura del Codice](#struttura-del-codice)
- [Configurazione](#configurazione)
- [Esecuzione](#esecuzione)
- [Dettaglio delle Funzioni Principali](#dettaglio-delle-funzioni-principali)
- [API HTTP](#api-http)
- [Log Accessi](#log-accessi)
- [Note di Sicurezza](#note-di-sicurezza)

---

## Requisiti

- Raspberry Pi con PiCamera2
- Python 3
- Librerie Python: `face_recognition`, `opencv-python`, `numpy`, `picamera2`, `gpiozero`
- File di codifiche facciali (`encodings.pickle`)
- Directory `public_web` con file `index.html` e `accessi.txt`

---

## Funzionalità

- **Riconoscimento facciale** in tempo reale tramite PiCamera2
- **Apertura porta** tramite relè collegato al GPIO
- **Web server HTTP** per comando apertura porta e visualizzazione pagina web
- **Log degli accessi** con timestamp, utente e stato

---

## Struttura del Codice

- **Configurazione**: parametri principali (nomi autorizzati, pin GPIO, porta HTTP, ecc.)
- **Setup**: caricamento codifiche facciali, inizializzazione camera e GPIO
- **Loop di riconoscimento facciale**: acquisizione frame, riconoscimento, apertura porta
- **Server HTTP**: gestisce richieste GET e POST per apertura porta tramite password
- **Log accessi**: scrive su file ogni tentativo di accesso

---

## Configurazione

Modifica i seguenti parametri secondo le tue esigenze:

AUTHORIZED_NAMES = ["andi", "K_nex"] # Nomi autorizzati (case-sensitive)
GPIO_PIN = 26 # Pin GPIO collegato al relè
HTTP_PORT = 8000 # Porta del server HTTP
ENCODINGS_FILE = "encodings.pickle" # File con codifiche facciali


Assicurati che il file `encodings.pickle` sia presente e contenga le codifiche generate con la libreria `face_recognition`.

---

## Esecuzione

1. **Assicurati che la camera sia collegata e abilitata**
2. **Posiziona il file `encodings.pickle` nella directory del progetto**
3. **Crea la cartella `public_web` con `index.html` e `accessi.txt`**
4. **Installa le dipendenze Python**
5. **Esegui lo script:**

python3 scriptCompleto.py


---

## Dettaglio delle Funzioni Principali

### `open_door(duration=5)`
Apre la porta (attiva il relè) per il numero di secondi specificato, evitando aperture multiple concorrenti tramite un lock.

### `save_log(utente, status)`
Scrive su file di log ogni tentativo di accesso con timestamp, nome utente e stato (ENTRATO/NEGATO).

### `process_frame(frame)`
- Ridimensiona e converte il frame per il riconoscimento facciale
- Confronta i volti rilevati con quelli noti
- Se un volto autorizzato viene riconosciuto, avvia l'apertura della porta e logga l'accesso

### `face_recognition_loop()`
Ciclo continuo che acquisisce frame dalla camera e li processa per il riconoscimento facciale.

### `SimpleHTTPRequestHandler`
Gestisce richieste HTTP:
- **GET /**: restituisce la pagina web principale
- **POST /apri**: consente l'apertura della porta tramite password segreta

### `run_http_server()`
Avvia il server HTTP sulla porta configurata.

---

## API HTTP

### POST `/apri`

Permette di aprire la porta inviando una richiesta POST con JSON:

#### Richiesta

{
"utente": "nome_utente",
"parola_dordine": "apriti sesamo"
}


#### Risposta
- **200 OK** e testo "Accesso Consentito! Corri!!!" se la password è corretta
- **200 OK** e testo "Accesso Negato!" se la password è errata

---

## Log Accessi

Tutti i tentativi di accesso vengono registrati in `public_web/accessi.txt` nel formato:

Time: 2024-04-25 18:00:00 - Utente: andi - Status: ENTRATO


---

## Note di Sicurezza

- La password per l'accesso remoto è in chiaro: **non utilizzare in ambienti non protetti**
- Il sistema non implementa HTTPS né autenticazione avanzata
- Per produzione, prevedere controlli di sicurezza aggiuntivi

---

## Esempio di Avvio


---

## Credits

Sviluppato da [Roland Gjopalaj]  
Basato su: [face_recognition](https://github.com/ageitgey/face_recognition), [PiCamera2](https://github.com/raspberrypi/picamera2), [gpiozero](https://gpiozero.readthedocs.io/)


