from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from gpiozero import LED
import time
import threading  # Aggiungiamo il modulo threading
from datetime import datetime  # Aggiunta per il timestamp

# Initialize GPIO
output = LED(19)
flag_porta = False

HOST = ''
PORT = 8000

def openDoor():
    global flag_porta
    output.on()  # Accende il pin
    time.sleep(5) # Aspetta 5 secondi
    output.off()  # Spegne il pin
    flag_porta = False  # Aggiorna lo stato
    
def closeDoor():
    output.off()  # Spegne il Pin

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('public_web/index.html', 'rb') as file:
                html_content = file.read()
            self.wfile.write(html_content)
        else:
            self.send_error(404, "File Not Found: %s" % self.path)

    def do_POST(self):
        global flag_porta
        status = ""
        if self.path == '/apri':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data_bytes = self.rfile.read(content_length)
                post_data_str = post_data_bytes.decode('utf-8')

                data = json.loads(post_data_str)
                print(data)
                utente = data.get("utente")
                parola_dordine = data.get("parola_dordine")
                
                if parola_dordine == "apriti sesamo":
                    flag_porta = True 
                    # Avvia l'apertura della porta in un thread separato
                    threading.Thread(target=openDoor).start()
                    status = "ENTRATO"
                else:
                    flag_porta = False 
                    closeDoor()
                    status = "NEGATO"

                # Invia immediatamente la risposta
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Accesso Consentito! Corri!!!" if flag_porta else b"Accesso Negato!")


                #salva i log nel file accessi.txt
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                with open('public_web/accessi.txt', 'a') as log_file:
                    log_file.write(f"Time: {timestamp} - Utente: {utente} - Status: {status}\n")

            except Exception as e:
                print(f"Errore durante l'elaborazione della richiesta POST: {e}")
                self.send_error(500, "Errore interno del server")
        else:
            self.send_error(404, "Endpoint Not Found: %s" % self.path)

def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, addr=HOST, port=PORT):
    server_address = (addr, port)
    httpd = server_class(server_address, handler_class)
    print(f"Avvio del server su http://localhost:{port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer fermato.")
        httpd.server_close()

if __name__ == '__main__':
    run()
