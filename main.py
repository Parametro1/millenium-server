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
            
            # Generazione minimale e sicura della pagina senza stringhe multilinea inclini a errori
            html_parts = [
                "<!DOCTYPE html><html><head><title>Millenium Terminal</title>",
                "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
                "<style>body{font-family:sans-serif; background:#010409; color:#c9d1d9; padding:20px;}",
                ".card{background:#0d1117; padding:15px; border-radius:8px; border:1px solid #21262d; margin-bottom:15px;}",
                "h1{color:#f0f6fc;} h2{color:#58a6ff; border-bottom:1px solid #21262d; padding-bottom:5px;}",
                "table{width:100%; border-collapse:collapse;} td,th{padding:10px; border-bottom:1px solid #21262d; text-align:left;}",
                ".badge{background:#161b22; padding:4px 8px; border-radius:4px; font-weight:bold; color:#58a6ff;}",
                "</style></head><body>",
                "<div style='max-width:1200px; margin:0 auto;'>",
                "<h1>⚡ Millenium Intelligence Terminal</h1>",
                "<div class='card'>📊 <b>Stato Radar:</b> Connesso | 🔄 <b>Ultimo Aggiornamento:</b> <span id='lu'>-</span> | 🎯 <b>Scansionati:</b> <span id='ps'>0</span></div>",
                "<h2>🔴 Live Stream Rilevanti</h2>",
                "<table><thead><tr><th>Minuto</th><th>Match</th><th>Punteggio</th><th>Suggerimento</th></tr></thead><tbody id='live-rows'></tbody></table>",
                "</div>",
                "<script>",
                "async function update(){",
                "  try{",
                "    let res = await fetch('/api/data'); let d = await res.json();",
                "    document.getElementById('lu').innerText = d.ultimo_aggiornamento;",
                "    document.getElementById('ps').innerText = d.partite_scansionate;",
                "    let html = '';",
                "    if(!d.match_rilevanti || d.match_rilevanti.length === 0){",
                "      html = '<tr><td colspan=\"4\" style=\"text-align:center; color:#8b949e;\">Nessun match live con parametri minimi soddisfatti.</td></tr>';",
                "    } else {",
                "      d.match_rilevanti.forEach(m => {",
                "        html += '<tr><td><span class=\"badge\">' + m.orario + '</span></td><td><b>' + m.partita + '</b><br><small style=\"color:#8b949e;\">' + m.campionato + '</small></td><td>' + m.punteggio + '</td><td style=\"background:#161b22; border-radius:4px;\">' + m.analisi + '</td></tr>';",
                "      });",
                "    }",
                "    document.getElementById('live-rows').innerHTML = html;",
                "  }catch(e){console.error(e);}",
                "}",
                "setInterval(update, 15000); window.onload = update;",
                "</script></body></html>"
            ]
            self.wfile.write("".join(html_parts).encode("utf-8"))
        else:
            self.send_error(404, "File Not Found")

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
            somma_medie = media_casa + media_fuori
            
            output = f"🏠 Media Casa: {media_casa:.2f} | 🚀 Media Fuori: {media_fuori:.2f}<br>"
            if is_live and minuto is not None:
                if somma_medie >= 2.40:
                    if minuto <= 35: output += "<b>💰 CONSIGLIO: OVER 0.5 HT (Quota > 1.70)</b>"
                    elif minuto <= 65: output += f"<b>💰 CONSIGLIO: OVER {gol_totali + 1.5} LIVE</b>"
                    elif minuto <= 82: output += f"<b>💰 CONSIGLIO: OVER {gol_totali + 0.5} FINALE</b>"
                    else: output += "<i>No Bet (Fine match)</i>"
                else: output += "<i>No Bet (Storico basso)</i>"
            else:
                if somma_medie >= 3.20: output += "<b>STUDIO: Pendenza OVER 2.5</b>"
                elif somma_medie >= 2.40: output += "<b>STUDIO: Ottimo OVER 1.5</b>"
                else: output += "<i>STUDIO: Match da Under</i>"
            return output
        return "File archivio non trovato."
    except Exception: return "Errore calcolo medie."

def scansione_prematch():
    try:
        response = session.get(URL_FUTURE, timeout=15)
        if response.status_code == 200:
            partite = response.json().get("Value", [])
            prossimi_match = []
            for partita in partite:
                campionato = partita.get("L", "")
                squadra_casa = partita.get("O1", "")
                squadra_ospite = partita.get("O2", "")
                timestamp_inizio = partita.get("S", 0)
                if campeonato in DIZIONARIO_CAMPIONATI and timestamp_inizio > 0:
                    nome_file_csv = DIZIONARIO_CAMPIONATI[campionato]
                    ora_inizio = time.strftime('%d/%m %H:%M', time.localtime(timestamp_inizio))
                    prossimi_match.append({
                        "data_ora": ora_inizio, "partita": f"{squadra_casa} - {squadra_ospite}",
                        "campionato": campionato, "analisi": analizza_e_consiglia(nome_file_csv, squadra_casa, squadra_ospite, is_live=False)
                    })
            DASHBOARD_DATA["match_futuri"] = prossimi_match
            salva_dati_su_file()
    except Exception as e: print(f"⚠️ Timeout Prematch: {e}", flush=True)

def scansione_partite_live():
    try:
        response = session.get(URL_LIVE, timeout=15)
        if response.status_code == 200:
            partite = response.json().get("Value", [])
            DASHBOARD_DATA["partite_scansionate"] = len(partite)
            DASHBOARD_DATA["ultimo_aggiornamento"] = time.strftime("%H:%M:%S")
            nuovi_match_rilevanti = []
            
            for partita in partite:
                campionato_live = partita.get("L", "")
                squadra_casa = partita.get("O1", "")
                squadra_ospite = partita.get("O2", "")
                if campeonato_live in DIZIONARIO_CAMPIONATI:
                    nome_file_csv = DIZIONARIO_CAMPIONATI[campionato_live]
                    sc_data = partita.get("SC", {})
                    tempo_secondi = sc_data.get("TS", 0)
                    minuto_corrente = int(tempo_secondi // 60) if tempo_secondi > 0 else 1
                    gol_casa, gol_ospite = int(sc_data.get("FS", {}).get("G1", 0)), int(sc_data.get("FS", {}).get("G2", 0))
                    totale_gol_attuali = gol_casa + gol_ospite
                    
                    tiri_porta_casa, tiri_porta_ospite = 0, 0
                    tiri_fuori_casa, tiri_fuori_ospite = 0, 0
                    ap_casa, ap_ospite = 0, 0
                    
                    for stat in sc_data.get("S", []):
                        tipo_stat = stat.get("T")
                        if tipo_stat == 2:
                            tiri_porta_casa, tiri_porta_ospite = int(stat.get("G1", 0
