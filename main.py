from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import os
import time
import requests
from threading import Thread
import json

# --- CONFIGURAZIONI ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def invia_telegram(messaggio):
    if not TOKEN or not CHAT_ID: return
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": messaggio}, timeout=5)
    except: pass

class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        # Questa è la veste grafica del tuo Millenium Terminal
        res = "<html><head><style>body{background:#0b0f19; color:#e2e8f0; font-family:sans-serif; padding:20px;}</style></head><body><h1>⚡ MILLENIUM TERMINAL</h1><p>Sistema Online e attivo.</p></body></html>"
        self.wfile.write(res.encode("utf-8"))

def avvia_server():
    porta = int(os.environ.get("PORT", 10000))
    with TCPServer(("0.0.0.0", porta), DashboardHandler) as server:
        server.serve_forever()

def scansione():
    while True:
        print("Ciclo di scansione attivo...", flush=True)
        time.sleep(60)

if __name__ == "__main__":
    Thread(target=avvia_server, daemon=True).start()
    Thread(target=scansione, daemon=True).start()
    invia_telegram("Test: Il bot è connesso e funzionante!")
