from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import os
import time
import requests
import pandas as pd
from threading import Thread

# Configurazione - Assicurati di aver impostato le variabili d'ambiente su Render!
TOKEN = os.getenv("TELEGRAM_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
URL_LIVE = "https://1xbet.com/LiveFeed/GetMatchesVzip?sports=1&count=50&lng=it"
URL_FUTURE = "https://1xbet.com/LineFeed/GetMatchesVzip?sports=1&count=50&lng=it"

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

DASHBOARD_DATA = {"ultimo_aggiornamento": "Mai", "partite_scansionate": 0, "match_rilevanti": [], "match_futuri": []}

DIZIONARIO_CAMPIONATI = {
    "Calcio. Italia. Serie A": "I1", "Calcio. Italia. Serie B": "I2", "Calcio. Inghilterra. Premier League": "E0",
    "Calcio. Inghilterra. Championship": "E1", "Calcio. Spagna. Primera Division": "SP1", "Calcio. Spagna. Segunda Division": "SP2",
    "Calcio. Germania. Bundesliga": "D1", "Calcio. Germania. 2. Bundesliga": "D2", "Calcio. Francia. Ligue 1": "F1",
    "Calcio. Francia. Ligue 2": "F2", "Calcio. Olanda. Eredivisie": "N1", "Calcio. Turchia. SuperLig": "T1", "Calcio. USA. MLS": "USA"
}

class DashboardHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args): return
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write("<html><body><h1>Millenium Bot Online</h1><p>Sistema di analisi attivo.</p></body></html>".encode("utf-8"))

def finto_server():
    porta = int(os.environ.get("PORT", 10000))
    with TCPServer(("0.0.0.0", porta), DashboardHandler) as server:
        server.serve_forever()

def analizza_e_consiglia(nome_file_csv, casa_live, ospite_live, minuto=None, gol_totali=0, is_live=False):
    file_path = f"{nome_file_csv}.csv" if os.path.exists(f"{nome_file_csv}.csv") else f"{nome_file_csv}.CSV"
    if not os.path.exists(file_path): return "Archivio non trovato."
    try:
        df = pd.read_csv(file_path)
        pc = df[df['HomeTeam'].str.contains(casa_live, case=False, na=False)]
        po = df[df['AwayTeam'].str.contains(ospite_live, case=False, na=False)]
        mc = pc['FTHG'].mean() if not pc.empty and 'FTHG' in df.columns else 0
        mf = po['FTAG'].mean() if not po.empty and 'FTAG' in df.columns else 0
        somma = mc + mf
        if is_live:
            if somma >= 2.40:
                if minuto <= 35: return "CONSIGLIO: OVER 0.5 HT"
                elif minuto <= 65: return "CONSIGLIO: OVER LIVE"
                return "CONSIGLIO: OVER FINALE"
            return "No Bet (Storico basso)"
        return f"Media Gol: {somma:.2f}"
    except: return "Errore analisi."

def invia_telegram(messaggio):
    if not TOKEN: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": messaggio, "parse_mode": "Markdown"})

def scansione_live():
    try:
        resp = requests.get(URL_LIVE, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            for partita in resp.json().get("Value", []):
                if partita.get("L") in DIZIONARIO_CAMPIONATI:
                    # Logica di scansione semplificata per stabilità
                    pass
    except: pass

if __name__ == "__main__":
    Thread(target=finto_server, daemon=True).start()
    while True:
        scansione_live()
        time.sleep(60)
