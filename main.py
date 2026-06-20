import os
import time
import requests
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from threading import Thread

# Configurazione forzata
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def invia_messaggio_subito():
    print("DEBUG: Provo a inviare messaggio...", flush=True)
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        try:
            r = requests.post(url, json={"chat_id": CHAT_ID, "text": "✅ Il bot è partito correttamente!"})
            print(f"DEBUG TELEGRAM: Risposta {r.status_code} - {r.text}", flush=True)
        except Exception as e:
            print(f"DEBUG ERRORE: {e}", flush=True)
    else:
        print("DEBUG ERRORE: TOKEN o CHAT_ID mancanti!", flush=True)

def avvia_server():
    porta = int(os.environ.get("PORT", 10000))
    with TCPServer(("0.0.0.0", porta), SimpleHTTPRequestHandler) as server:
        server.serve_forever()

if __name__ == "__main__":
    # Invio messaggio prima di tutto
    invia_messaggio_subito()
    # Poi avvio il server
    avvia_server()
