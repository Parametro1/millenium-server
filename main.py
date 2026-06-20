from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import os
import time
import requests
from threading import Thread

# --- CONFIGURAZIONI ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def invia_telegram(messaggio):
    if not TOKEN or not CHAT_ID: return
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": messaggio}, timeout=5)
    except: pass

# Questa classe gestisce la tua grafica "Millenium Terminal"
class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        res = "<html><head><style>body{background:#0b0f19; color:#38bdf8; font-family:sans-serif; padding:20px;} h1{border-bottom:1px solid #1e293b;}</style></head><body><h1>⚡ MILLENIUM TERMINAL</h1><p>Sistema attivo e in ascolto.</p></body></html>"
        self.wfile.write(res.encode("utf-8"))

def avvia_server():
    porta = int(os.environ.get("PORT", 10000))
    # Usiamo DashboardHandler per la grafica
    with TCPServer(("0.0.0.0", porta), DashboardHandler) as server:
        server.serve_forever()

def scansione():
    while True:
        print("Ciclo di scansione attivo...", flush=True)
        # Qui in futuro aggiungerai la logica di analisi CSV
        time.sleep(60)

if __name__ == "__main__":
    Thread(target=avvia_server, daemon=True).start()
    Thread(target=scansione, daemon=True).start()
    invia_telegram("Test: Il bot è connesso e funzionante!")
