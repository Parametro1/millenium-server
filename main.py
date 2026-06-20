import os
import time
import requests
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from threading import Thread

# Recupera i dati da Render
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def invia_telegram(messaggio):
    if TOKEN and CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(url, json={"chat_id": CHAT_ID, "text": messaggio}, timeout=10)
        except Exception as e:
            print(f"Errore Telegram: {e}", flush=True)

def avvia_server():
    porta = int(os.environ.get("PORT", 10000))
    with TCPServer(("0.0.0.0", porta), SimpleHTTPRequestHandler) as server:
        server.serve_forever()

def scansione():
    # Invio di avvio
    invia_telegram("✅ Il Bot è online!")
    while True:
        print("Il bot sta girando...", flush=True)
        time.sleep(60)

if __name__ == "__main__":
    Thread(target=avvia_server, daemon=True).start()
    scansione()
