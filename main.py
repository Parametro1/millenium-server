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

# ==========================================
# SERVER WEB PER RENDER (KEEP-ALIVE)
# ==========================================
class DashboardHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args): return
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        html = """<!DOCTYPE html>
        <html>
        <head><title>Millenium Terminal</title></head>
        <body style="background:#010409; color:#c9d1d9; font-family:sans-serif; padding:20px; text-align:center;">
            <h1 style="color:#58a6ff;">Millenium Trading Terminal</h1>
            <p>Status: <span style="color:#238636; font-weight:bold;">ACTIVE</span></p>
            <p>Il motore di scansione sta girando in background su Render.</p>
        </body>
        </html>"""
        self.wfile.write(html.encode("utf-8"))
        return

def start_server():
    port = int(os.environ.get("PORT", 10000))
    with TCPServer(("0.0.0.0", port), DashboardHandler) as httpd:
        httpd.serve_forever()

# ==========================================
# MOTORE DI ANALISI E LOGICA DEL BOT
# ==========================================
def invia_telegram(messaggio):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        try:
            requests.post(url, json={"chat_id": CHAT_ID, "text": messaggio, "parse_mode": "Markdown"})
        except Exception as e:
            print(f"Errore Telegram: {e}", flush=True)

def analizza_archivio_storico(nome_file_csv, casa_live, ospite_live):
    file_standard = f"{nome_file_csv}.csv"
    if os.path.exists(file_standard):
        try:
            df = pd.read_csv(file_standard)
            partite_casa = df[df['HomeTeam'].str.contains(casa_live, case=False, na=False)]
            partite_ospite = df[df['AwayTeam'].str.contains(ospite_live, case=False, na=False)]
            
            output = ""
            if not partite_casa.empty and 'FTHG' in df.columns:
                media_fatti_casa = partite_casa['FTHG'].mean()
                output += f"🏠 {casa_live} (In Casa) Media Gol Fatti: *{media_fatti_casa:.2f}*\n"
            else:
                output += f"🏠 Dati storici in casa per {casa_live} insufficienti.\n"
                
            if not partite_ospite.empty and 'FTAG' in df.columns:
                media_fatti_ospite = partite_ospite['FTAG'].mean()
                output += f"🚀 {ospite_live} (Fuori Casa) Media Gol Fatti: *{media_fatti_ospite:.2f}*"
            else:
                output += f"🚀 Dati storici fuori casa per {ospite_live} insufficienti."
            return output
        except Exception as e:
            return f"⚠️ Errore lettura CSV: {e}"
    return "⚠️ File CSV di campionato non trovato."

def scansione_partite():
    print("Scansione partite live in corso...", flush=True)
    try:
        response = session.get(URL_LIVE, timeout=10)
        if response.status_code == 200:
            partite = response.json().get("Value", [])
            for partita in partite:
                campionato_live = partita.get("LEAG", "")
                squadra_casa = partita.get("O1", "")
                squadra_ospite = partita.get("O2", "")
                
                if campeonato_live in DIZIONARIO_CAMPIONATI:
                    nome_file_csv = DIZIONARIO_CAMPIONATI[campionato_live]
                    
                    stats = partita.get("SC", {}).get("S", [])
                    tiri_totali_live = 0
                    for s in stats:
                        if s.get("Type") == 2:  # ID Tiri in porta
                            tiri_totali_live = int(s.get("All1", 0)) + int(s.get("All2", 0))
                    
                    if tiri_totali_live >= 5:
                        analisi_storica = analizza_archivio_storico(nome_file_csv, squadra_casa, squadra_ospite)
                        messaggio = (
                            f"⚽ *MILLENIUM BOT - SEGNALE VALUE BET*\n\n"
                            f"🏆 Campionato: *{campionato_live}*\n"
                            f"⚔️ Match: *{squadra_casa} vs {squadra_ospite}*\n"
                            f"🔥 Tiri in Porta Live: *{tiri_totali_live}*\n\n"
                            f"{analisi_storica}"
                        )
                        invia_telegram(messaggio)
                        print(f"Segnale inviato su Telegram per: {squadra_casa} - {squadra_ospite}", flush=True)
                        time.sleep(5)
    except Exception as e:
        print(f"Errore durante lo screening live: {e}", flush=True)

# ==========================================
# AVVIO REALE DEI PROCESSI
# ==========================================
Thread(target=start_server, daemon=True).start()
print("Millenium Bot avviato e pronto a calcolare!", flush=True)

while True:
    scansione_partite()
    time.sleep(60)
