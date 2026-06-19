from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import os
import time
import requests
import pandas as pd
from threading import Thread
import json

# ==========================================
# CONFIGURAZIONI PRINCIPALI
# ==========================================
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
URL_LIVE = "https://1xbet.com/LiveFeed/GetMatchesVzip?sports=1&count=50&lng=it"
URL_FUTURE = "https://1xbet.com/LineFeed/GetMatchesVzip?sports=1&count=50&lng=it"
DATA_FILE = "dashboard_data.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
}

session = requests.Session()
session.headers.update(HEADERS)

adapter = requests.adapters.HTTPAdapter(max_retries=2)
session.mount("https://", adapter)

if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            DASHBOARD_DATA = json.load(f)
    except Exception:
        DASHBOARD_DATA = {"ultimo_aggiornamento": "Mai", "partite_scansionate": 0, "alert_inviati_totale": 0, "match_rilevanti": [], "match_futuri": []}
else:
    DASHBOARD_DATA = {"ultimo_aggiornamento": "Mai", "partite_scansionate": 0, "alert_inviati_totale": 0, "match_rilevanti": [], "match_futuri": []}

DIZIONARIO_CAMPIONATI = {
    "Calcio. Inghilterra. Premier League": "E0", "Calcio. Inghilterra. Championship": "E1",
    "Calcio. Inghilterra. League One": "E2", "Calcio. Inghilterra. League Two": "E3",
    "Calcio. Inghilterra. National League": "EC", "Calcio. Germania. Bundesliga": "D1",
    "Calcio. Germania. 2. Bundesliga": "D2", "Calcio. Germania. 3. Liga": "D3",
    "Calcio. Italia. Serie A": "I1", "Calcio. Italia. Serie B": "I2",
    "Calcio. Spagna. Primera Division": "SP1", "Calcio. Spagna. Segunda Division": "SP2",
    "Calcio. Francia. Ligue 1": "F1", "Calcio. Francia. Ligue 2": "F2",
    "Calcio. Olanda. Eredivisie": "N1", "Calcio. Olanda. Eerste Divisie": "N2",
    "Calcio. Portogallo. Primeira Liga": "P1", "Calcio. Turchia. SuperLig": "T1",
    "Calcio. Belgio. Pro League": "B1", "Calcio. Scozia. Premiership": "SC0",
    "Calcio. Scozia. Championship": "SC1", "Calcio. Grecia. Super League": "G1",
    "Calcio. Austria. Bundesliga": "A1", "Calcio. Svizzera. Super League": "SW1",
    "Calcio. Danimarca. Superligaen": "DN1", "Calcio. Norvegia. Eliteserien": "N1",
    "Calcio. Svezia. Allsvenskan": "S1", "Calcio. USA. MLS": "USA"
}

def salva_dati_su_file():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(DASHBOARD_DATA, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Errore JSON: {e}", flush=True)

class DashboardHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args): return
    def do_GET(self):
        if self.path == "/api/data":
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(DASHBOARD_DATA).encode("utf-8"))
            return
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            
            # Struttura iper-semplificata priva di virgolette triple lunghe
            res_html = "<html><head><title>Terminal</title></head><body style='font-family:sans-serif;background:#0d1117;color:#c9d1d9;padding:20px;'>"
            res_html += "<h1>⚡ Millenium Terminal ⚡</h1>"
            res_html += "<div><p><b>Ultimo Aggiornamento:</b> " + str(DASHBOARD_DATA["ultimo_aggiornamento"]) + "</p>"
            res_html += "<p><b>Partite Scansionate:</b> " + str(DASHBOARD_DATA["partite_scansionate"]) + "</p></div>"
            res_html += "<h2>Partite Live Rilevanti</h2><ul>"
            
            if not DASHBOARD_DATA["match_rilevanti"]:
                res_html += "<li>Nessun match attivo con i parametri minimi richiesti.</li>"
            else:
                for m in DASHBOARD_DATA["match_rilevanti"]:
                    res_html += "<li><b>" + str(m["partita"]) + "</b> (" + str(m["orario"]) + ") - Risultato: " + str(m["punteggio"]) + "<br>" + str(m["analisi"]) + "</li>"
            
            res_html += "</ul><script>setTimeout(function(){ location.reload(); }, 15000);</script></body></html>"
            self.wfile.write(res_html.encode("utf-8"))
        else:
            self.send_error(404, "Not Found")

def finto_server():
    porta = int(os.environ.get("PORT", 10000))
    try:
        with TCPServer(("0.0.0.0", porta), DashboardHandler) as server:
            server.serve_forever()
    except Exception: pass

# =======================================================
# LOGICHE DI ANALISI STATISTICA
# =======================================================
def analizza_e_consiglia(nome_file_csv, casa_live, ospite_live, minuto=None, gol_totali=0, is_live=False):
    file_standard = f"{nome_file_csv}.csv"
    file_maiuscolo = f"{nome_file_csv}.CSV"
    nome_file = file_standard if os.path.exists(file_standard) else file_maiuscolo
    try:
        if os.path.exists(nome_file):
            df = pd.read_csv(nome_file)
            partite_casa = df[df['HomeTeam'].str.contains(casa_live, case=False, na=False)]
            partite_ospite = df[df['AwayTeam'].str.contains(ospite_live, case=False, na=False)]
            media_casa = partite_casa['FTHG'].mean() if not partite_casa.empty and 'FTHG' in df.columns else 0.0
            media_fuori = partite_ospite['FTAG'].mean() if not partite_ospite.empty and 'FTAG' in df.columns else 0.0
            somma_medie =
