import os
import time
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from threading import Thread

# Server web super leggero
def avvia_server():
    porta = int(os.environ.get("PORT", 10000))
    # Usiamo SimpleHTTPRequestHandler per evitare errori complessi
    with TCPServer(("0.0.0.0", porta), SimpleHTTPRequestHandler) as server:
        server.serve_forever()

def scansione():
    while True:
        print("Il bot sta girando...", flush=True)
        time.sleep(60)

if __name__ == "__main__":
    # Avvia il server web in un thread separato
    Thread(target=avvia_server, daemon=True).start()
    # Avvia il ciclo di scansione
    scansione()
