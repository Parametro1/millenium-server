from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import os
import time
import requests
import pandas as pd
from threading import Thread
import json
from datetime import datetime, timedelta

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

CAMPIONATI_ALL = list(DIZIONARIO_CAMPIONATI.values())

def salva_dati_su_file():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(DASHBOARD_DATA, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"⚠️ Errore salvataggio JSON: {e}", flush=True)

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
            
            badge_campionati = "".join([f'<span class="db-league-badge">{sigla}</span>' for sigla in CAMPIONATI_ALL])
            righe_campionati_html = "".join([f'<tr><td style="color:#58a6ff; font-weight:700; border-bottom: 1px solid #161b22;">{sigla}</td><td style="color:#8b949e; border-bottom: 1px solid #161b22;">{nome}</td></tr>' for nome, sigla in DIZIONARIO_CAMPIONATI.items()])

            giorni_list = []
            nomi_giorni = ["Dom", "Lun", "Mar", "Mer", "Gio", "Ven", "Sab"]
            oggi = datetime.now()
            for i in range(7):
                d = oggi + timedelta(days=i)
                tag = "OGGI" if i == 0 else ("DOMANI" if i == 1 else f"{nomi_giorni[d.weekday()]} {d.strftime('%d/%m')}")
                giorni_list.append({"id": d.strftime("%d/%m"), "label": tag, "is_oggi": i == 0})
            
            giorni_json = json.dumps(giorni_list)
            len_campionati = str(len(CAMPIONATI_ALL))

            # HTML STRUTTURATO COME STRINGA STANDARD SENZA F-STRING PER EVITARE SYNTAX ERROR
            html = """<!DOCTYPE html>
<html>
<head>
    <title>Millenium — Professional Trading Terminal</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #010409; color: #c9d1d9; margin:0; padding:25px; box-sizing: border-box; }
        .container { max-width: 1700px; margin: 0 auto; }
        .header { background: #0d1117; padding: 20px 30px; border-radius: 12px; border: 1px solid #21262d; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; }
        h1 { color: #f0f6fc; margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.5px; display: flex; align-items: center; gap: 10px; }
        .status-bar { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
        .badge { background: #161b22; color: #8b949e; padding: 8px 14px; border-radius: 6px; border: 1px solid #30363d; font-size: 13px; font-weight: 600; }
        .badge span { color: #58a6ff; font-weight: 700; }
        .badge-online { background: rgba(46, 160, 67, 0.15); color: #3fb950; border-color: rgba(56, 139, 253, 0.15); }
        .badge-live-count { background: rgba(248, 81, 73, 0.1); color: #f85149; border-color: rgba(248, 81, 73, 0.2); }
        .controls-panel { background: #0d1117; border: 1px solid #21262d; padding: 20px; border-radius: 12px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; gap: 20px; flex-wrap: wrap; }
        .search-box { background: #010409; border: 1px solid #30363d; color: #f0f6fc; padding: 10px 16px; border-radius: 6px; font-size: 14px; width: 320px; transition: border-color 0.2s; }
        .search-box:focus { outline: none; border-color: #58a6ff; }
        .db-info { display: flex; flex-direction: column; gap: 8px; flex: 1; max-width: 70%; }
        .db-title { font-size: 11px; color: #8b949e; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
        .badge-container { display: flex; gap: 6px; flex-wrap: wrap; }
        .db-league-badge { background: #161b22; color: #c9d1d9; font-weight: 600; font-size: 11px; padding: 4px 8px; border-radius: 4px; border: 1px solid #30363d; }
        .calendar-section { background: #0d1117; border: 1px solid #21262d; padding: 20px; border-radius: 12px; margin-bottom: 25px; }
        .calendar-title { font-size: 12px; font-weight: 700; text-transform: uppercase; color: #d29922; margin-bottom: 15px; letter-spacing: 0.5px; }
        .calendar-grid { display: flex; gap: 10px; flex-wrap: wrap; }
        .cal-btn { flex: 1; min-width: 125px; padding: 12px 8px; border-radius: 6px; border: 1px solid #21262d; background: #161b22; text-align: center; cursor: pointer; font-weight: 600; font-size: 13px; transition: all 0.2s ease; }
        .cal-btn .cal-sub { font-size: 11px; font-weight: 500; margin-top: 3px; display
