import requests
import json

def inviaDatiAlServer(url_server, dati_da_inviare):
    print(f"--- Invio richiesta POST a: {url_server} ---")

    try:
        # Invia la richiesta POST
        response = requests.post(url_server, json=dati_da_inviare)

        response.raise_for_status()

        print(f"\n--- Risposta ricevuta dal server ---")
        print(f"Status Code: {response.status_code}") # Stampa lo status code (es. 200)

        try:
            # Prova a decodificare la risposta JSON ricevuta
            risposta_json = response.json()
            print("Corpo della risposta (JSON):")
            # Stampa il JSON ricevuto formattato in modo leggibile
            print(json.dumps(risposta_json, indent=2))
        except json.JSONDecodeError:
            # Se la risposta non è JSON valido
            print("Errore: La risposta del server non è in formato JSON valido.")
            print("Contenuto della risposta (testo):")
            print(response.text)

    except requests.exceptions.ConnectionError as e:
        print(f"\n--- Errore ---")
        print(f"Errore di connessione: Impossibile raggiungere il server a {url_server}")
        print("Verifica che il server Node.js sia in esecuzione sulla porta corretta.")
        # print(f"Dettagli: {e}") # Decommenta per dettagli tecnici
    except requests.exceptions.Timeout:
        print(f"\n--- Errore ---")
        print("Errore: La richiesta è andata in timeout.")
    except requests.exceptions.HTTPError as e:
        # Cattura errori sollevati da response.raise_for_status()
        print(f"\n--- Errore HTTP ---")
        print(f"Status Code di errore: {e.response.status_code}")
        print(f"Motivo: {e.response.reason}")
        print("Corpo della risposta (se presente):")
        print(e.response.text)
    except requests.exceptions.RequestException as e:
        # Cattura qualsiasi altra eccezione legata alla richiesta
        print(f"\n--- Errore ---")
        print(f"Si è verificato un errore durante l'invio della richiesta: {e}")
##################################################################################################


# URL dell'endpoint POST sul tuo server Node.js
url_server = "http://192.168.10.128:80/api/data"

inviaDatiAlServer(url_server, {"kot": "provaaaaaaaaaaaaa"})