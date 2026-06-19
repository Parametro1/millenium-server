from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import os
import time
import requests
import pandas as pd
from threading import Thread
import json
import calendar
from datetime import datetime

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

DASHBOARD_DATA = {
    "ultimo_aggiornamento": "Mai",
    "partite_scansionate": 0,
    "alert_inviati_totale": 0,
    "match_rilevanti": [],
    "match_futuri": []
}

if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            DASHBOARD_DATA = json.load(f)
    except Exception:
        pass

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

def genera_html_calendario():
    oggi = datetime.now()
    anno = oggi.year
    mese = oggi.month
    giorno_oggi = oggi.day
    
    nomi_mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    cal = calendar.monthcalendar(anno, mese)
    
    html = f"<div class='cal-box'>"
    html += f"<div class='cal-title'>📅 {nomi_mesi[mese-1].upper()} {anno}</div>"
    html += "<div class='cal-grid cal-header-days'>"
    for d in ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]:
        html += f"<div>{d}</div>"
    html += "</div>"
    
    for week in cal:
        html += "<div class='cal-grid'>"
        for day in week:
            if day == 0:
                html += "<div class='cal-day empty'></div>"
            elif day == giorno_oggi:
                html += f"<div class='cal-day today'>{day}</div>"
            else:
                html += f"<div class='cal-day regular-day'>{day}</div>"
        html += "</div>"
    html += "</div>"
    return html

def genera_html_archivio():
    campionati_attivi = [m.get("campionato", "") for m in DASHBOARD_DATA.get("match_rilevanti", [])]
    
    html = "<div style='max-height: 400px; overflow-y: auto; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);'>"
    html += "<table style='margin-bottom:0;'><thead><tr><th>Stato</th><th>Lega</th><th>File</th></tr></thead><tbody id='archiveTable'>"
    for nome, codice in DIZIONARIO_CAMPIONATI.items():
        pulito = nome.replace("Calcio. ", "")
        
        if nome in campionati_attivi:
            stato = "<span class='badge-live-dot'></span><span style='color: #ef4444; font-weight:bold; font-size:11px;'>LIVE</span>"
            stile_testo = "color: #ff4d4d; font-weight: bold;"
        else:
            stato = "<span style='color:#10b981;'>🟢 Ready</span>"
            stile_testo = "color: #cbd5e1;"
            
        html += f"<tr><td>{stato}</td><td style='font-size:12px; {stile_testo}'><b>{pulito}</b></td><td><span class='badge' style='background:rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.15);'>{codice}.csv</span></td></tr>"
    html += "</tbody></table></div>"
    return html

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
            
            res = "<html><head><meta charset='utf-8'><title>Millenium Premium Terminal</title>"
            res += "<style>"
            # NUOVO SFONDO COLORATO SFUMATO DI LIVELLO PROFESSIONAL
            res += "body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #070a13 0%, #0f172a 40%, #05070c 100%); color: #e2e8f0; margin: 0; padding: 20px; min-height: 100vh; }"
            res += ".container { max-width: 1300px; margin: 0 auto; }"
            res += "h1 { color: #38bdf8; border-bottom: 2px solid rgba(56, 189, 248, 0.2); padding-bottom: 12px; margin-bottom: 25px; display: flex; align-items: center; justify-content: space-between; text-shadow: 0 0 15px rgba(56,189,248,0.2); }"
            res += ".layout-main { display: grid; grid-template-columns: 1fr 380px; gap: 30px; }"
            res += "@media (max-width: 1000px) { .layout-main { grid-template-columns: 1fr; } }"
            res += ".stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 25px; }"
            
            # EFFETTO VETRO (GLASSMORPHISM) SULLE CARD
            res += ".card { background: rgba(17, 24, 39, 0.7); backdrop-filter: blur(8px); border: 1px solid rgba(255, 255, 255, 0.08); padding: 18px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }"
            res += ".card h3 { margin: 0 0 6px 0; color: #94a3b8; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; }"
            res += ".card .value { font-size: 22px; font-weight: bold; color: #f8fafc; }"
            res += ".card .highlight { color: #10b981; text-shadow: 0 0 10px rgba(16,185,129,0.3); }"
            
            res += "h2 { color: #f1f5f9; font-size: 16px; margin-top: 0; margin-bottom: 15px; border-left: 4px solid #38bdf8; padding-left: 12px; text-transform: uppercase; letter-spacing: 0.05em; display: flex; align-items: center; justify-content: space-between; }"
            
            # TAVOLI CON LUNETTE E SFUMATURE
            res += "table { width: 100%; border-collapse: collapse; background: rgba(15, 23, 42, 0.6); border-radius: 12px; overflow: hidden; border: 1px solid rgba(255, 255, 255, 0.05); margin-bottom: 30px; }"
            res += "th { background: rgba(30, 41, 59, 0.85); color: #38bdf8; text-align: left; padding: 14px; font-size: 13px; font-weight: 600; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }"
            res += "td { padding: 14px; border-bottom: 1px solid rgba(255, 255, 255, 0.04); font-size: 13px; color: #cbd5e1; }"
            res += "tr:hover { background: rgba(56, 189, 248, 0.05); }"
            
            # FILTRO SEARCH BAR PROFESSONALE
            res += ".search-bar { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: white; border-radius: 6px; padding: 6px 12px; font-size: 12px; outline: none; width: 180px; transition: all 0.3s; }"
            res += ".search-bar:focus { border-color: #38bdf8; box-shadow: 0 0 8px rgba(56,189,248,0.3); width: 220px; }"
            
            # BADGES
            res += ".badge { background: #0284c7; color: white; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; border: 1px solid rgba(255,255,255,0.1); }"
            res += ".badge-live { background: #dc2626; box-shadow: 0 0 10px rgba(220,38,38,0.4); animation: pulse 2s infinite; }"
            res += ".badge-live-dot { height: 8px; width: 8px; background-color: #ef4444; border-radius: 50%; display: inline-block; margin-right: 6px; animation: pulse 1.2s infinite; }"
            
            # CALENDARIO PERSONALIZZATO
            res += ".cal-box { background: rgba(17, 24, 39, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 18px; text-align: center; margin-bottom: 25px; }"
            res += ".cal-title { font-weight: bold; color: #38bdf8; margin-bottom: 15px; font-size: 14px; letter-spacing: 0.07em; text-shadow: 0 0 10px rgba(56,189,248,0.1); }"
            res += ".cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; margin-bottom: 6px; }"
            res += ".cal-header-days { font-size: 11px; color: #64748b; font-weight: bold; margin-bottom: 12px; text-transform: uppercase; }"
            res += ".cal-day { padding: 9px 0; border-radius: 6px; font-size: 12px; font-family: monospace; font-weight: bold; transition: all 0.2s; }"
            res += ".cal-day.empty { background: transparent; }"
            res += ".cal-day.regular-day { background: #1e3a8a; color: #f59e0b; border: 1px solid rgba(245,158,11,0.1); }"
            res += ".cal-day.today { background: #ffffff; color: #10b981; box-shadow: 0 0 15px rgba(255,255,255,0.4); transform: scale(1.05); border: 1px solid #10b981; }"
            
            res += "@keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(0.96); } 100% { opacity: 1; transform: scale(1); } }"
            res += "</style></head><body><div class='container'>"
            
            # HEADER TERMINALE
            res += "<h1><span>⚡ MILLENIUM TERMINAL <span style='font-size:11px; background:rgba(16,185,129,0.1); color:#10b981; padding:3px 8px; border-radius:4px; margin-left:10px; border:1px solid rgba(16,185,129,0.2); vertical-align:middle;'>PREMIUM PRO</span></span> <span style='font-size:14px;color:#64748b;'>Engine: Online v2.4</span></h1>"
            
            # STATISTICHE CORRENTI
            res += "<div class='stats-grid'>"
            res += f"<div class='card'><h3>System Clock / Update</h3><div class='value' style='color:#38bdf8;'>⏱️ {DASHBOARD_DATA['ultimo_aggiornamento']}</div></div>"
            res += f"<div class='card'><h3>Scansione Flusso Core</h3><div class='value highlight'>{DASHBOARD_DATA['partite_scansionate']} <span style='font-size:12px;color:#64748b;font-weight:normal;'>match rilevati</span></div></div>"
            res += f"<div class='card'><h3>Notifiche Push Telegram</h3><div class='value' style='color:#f59e0b;'>🚀 {DASHBOARD_DATA['alert_inviati_totale']} <span style='font-size:12px;color:#64748b;font-weight:normal;'>inviati</span></div></div>"
            res += "</div>"
            
            # CORPO LAYOUT
            res += "<div class='layout-main'>"
            res += "<div class='col-left'>"
            
            # TABELLA MONITORAGGIO LIVE + FUNZIONE DI RICERCA
            res += "<h2><span>🔥 Monitoraggio Live</span> <input type='text' class='search-bar' id='searchLive' placeholder='Cerca match live...' onkeyup='filterTable(\"searchLive\", \"liveTable\")'></h2>"
            if not DASHBOARD_DATA["match_rilevanti"]:
                res += "<div style='background:rgba(17,24,39,0.5);padding:30px;border-radius:12px;border:1px solid rgba(255,255,255,0.05);color:#64748b;margin-bottom:30px;text-align:center;font-style:italic;'>Nessun match attivo soddisfa i filtri AP/Tiri impostati. In attesa di dati...</div>"
            else:
                res += "<table><thead><tr><th>Tempo</th><th>Incontro</th><th>Score</th><th>Consiglio / Archivio CSV</th></tr></thead><tbody id='liveTable'>"
                for m in DASHBOARD_DATA["match_rilevanti"]:
                    res += f"<tr><td><span class='badge badge-live'>{m['orario']}</span></td><td><b>{m['partita']}</b><br><span style='font-size:11px;color:#64748b;'>{m.get('campionato','-')}</span></td><td><span style='font-family:monospace;font-weight:bold;color:#f59e0b;font-size:14px;'>{m['punteggio']}</span></td><td>{m['analisi']}</td></tr>"
                res += "</tbody></table>"
            
            # TABELLA PALINSESTO + FUNZIONE DI RICERCA
            res += "<h2><span>📅 Palinsesto Prossimi Match</span> <input type='text' class='search-bar' id='searchPrematch' placeholder='Cerca prematch...' onkeyup='filterTable(\"searchPrematch\", \"prematchTable\")'></h2>"
            if not DASHBOARD_DATA.get("match_futuri"):
                res += "<div style='background:rgba(17,24,39,0.5);padding:30px;border-radius:12px;border:1px solid rgba(255,255,255,0.05);color:#64748b;text-align:center;font-style:italic;'>Palinsesto prematch momentaneamente vuoto o mercati chiusi.</div>"
            else:
                res += "<table><thead><tr><th>Ora Inizio</th><th>Incontro</th><th>Campionato</th><th>Analisi Prematch</th></tr></thead><tbody id='prematchTable'>"
                for mf in DASHBOARD_DATA["match_futuri"]:
                    res += f"<tr><td><span class='badge'>{mf['data_ora']}</span></td><td><b>{mf['partita']}</b></td><td><span style='color:#94a3b8;font-size:11px;'>{mf['campionato']}</span></td><td>{mf['analisi']}</td></tr>"
                res += "</tbody></table>"
                
            res += "</div>"
            
            # COLONNA DESTRA (CALENDARIO + ARCHIVIO)
            res += "<div class='col-right'>"
            res += "<h2>📆 Calendario Operativo</h2>"
            res += genera_html_calendario()
            
            res += "<h2 style='margin-top:20px;'>🗄️ Database Database (.CSV)</h2>"
            res += genera_html_archivio()
            res += "</div>"
            
            # FUNZIONI JAVASCRIPT AVANZATE DI RICERCA REAL-TIME
            res += "</div></div>"
            res += "<script>"
            res += "function filterTable(inputId, tableId) {"
            res += "  var input = document.getElementById(inputId);"
            res += "  var filter = input.value.toUpperCase();"
            res += "  var tbody = document.getElementById(tableId);"
            res += "  if(!tbody) return;"
            res += "  var rows = tbody.getElementsByTagName('tr');"
            res += "  for (var i = 0; i < rows.length; i++) {"
            res += "    var text = rows[i].textContent || rows[i].innerText;"
            res += "    if (text.toUpperCase().indexOf(filter) > -1) {"
            res += "      rows[i].style.display = '';"
            res += "    } else {"
            res += "      rows[i].style.display = 'none';"
            res += "    }"
            res += "  }"
            res += "}"
            res += "setTimeout(function(){ location.reload(); }, 15000);"
            res += "</script></body></html>"
            
            self.wfile.write(res.encode("utf-8"))
        else:
            self.send_error(404, "Not Found")

def avvia_server():
    porta = int(os.environ.get("PORT", 10000))
    try:
        with TCPServer(("0.0.0.0", porta), DashboardHandler) as server:
            server.serve_forever()
    except Exception: pass

def analizza_e_consiglia(nome_file_csv, casa_live, ospite_live, minuto=None, gol_totali=0, is_live=False):
    file_standard = f"{nome_file_csv}.csv"
    file_maiuscolo = f"{nome_file_csv}.CSV"
    nome_file = file_standard if os.path.exists(file_standard) else file_maiuscolo
    if not os.path.exists(nome_file):
        return "Nessun CSV trovato."
    try:
        df = pd.read_csv(nome_file)
        partite_casa = df[df['HomeTeam'].str.contains(casa_live, case=False, na=False)]
        partite_ospite = df[df['AwayTeam'].str.contains(ospite_live, case=False, na=False)]
        media_casa = float(partite_casa['FTHG'].mean()) if not partite_casa.empty and 'FTHG' in df.columns else 0.0
        media_fuori = float(partite_ospite['FTAG'].mean()) if not partite_ospite.empty and 'FTAG' in df.columns else 0.0
        somma_medie = media_casa + media_fuori
        output = f"Media: {somma_medie:.2f} (C:{media_casa:.1f} F:{media_fuori:.1f}) | "
        if is_live and minuto is not None:
            if somma_medie >= 2.40:
                if minuto <= 35: output += "<span style='color:#10b981;font-weight:bold;'>OVER 0.5 HT</span>"
                elif minuto <= 65: output += f"<span style='color:#10b981;font-weight:bold;'>OVER {gol_totali + 1.5} LIVE</span>"
                elif minuto <= 82: output += f"<span style='color:#10b981;font-weight:bold;'>OVER {gol_totali + 0.5} FINALE</span>"
                else: output += "No Bet"
            else: output += "No Bet (Storico basso)"
        else:
            if somma_medie >= 3.20: output += "STUDIO: OVER 2.5"
            elif somma_medie >= 2.40: output += "STUDIO: OVER 1.5"
            else: output += "STUDIO: UNDER"
        return output
    except Exception: return "Errore calcolo."

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
                    fs_data = sc_data.get("FS", {})
                    gol_casa, gol_ospite = int(fs_data.get("G1", 0)), int(fs_data.get("G2", 0))
                    totale_gol_attuali = gol_casa + gol_ospite
                    tiri_porta_casa, tiri_porta_ospite = 0, 0
                    tiri_totali, ap_totali = 0, 0
                    for stat in sc_data.get("S", []):
                        t = stat.get("T")
                        if t == 2: tiri_porta_casa, tiri_porta_ospite = int(stat.get("G1", 0)), int(stat.get("G2", 0))
                        elif t == 1: tiri_totali += int(stat.get("G1", 0)) + int(stat.get("G2", 0))
                        elif t == 3: ap_totali = int(stat.get("G1", 0)) + int(stat.get("G2", 0))
                    tiri_porta_totali = tiri_porta_casa + tiri_porta_ospite
                    tiri_totali += tiri_porta_totali
                    ap_al_minuto = round(ap_totali / minuto_corrente, 2) if minuto_corrente > 0 else 0.0
                    
                    if tiri_totali > 0 or ap_totali > 0:
                        analisi_output = analizza_e_consiglia(nome_file_csv, squadra_casa, squadra_ospite, minuto=minuto_corrente, gol_totali=totale_gol_attuali, is_live=True)
                        nuovi_match_rilevanti.append({
                            "orario": f"{minuto_corrente}'", "partita": f"{squadra_casa} - {squadra_ospite}",
                            "punteggio": f"{gol_casa} - {gol_ospite}", "campionato": campeonato_live, "analisi": analisi_output
                        })
                        if (ap_al_minuto >= 1.15 and minuto_corrente >= 15 and tiri_totali >= 4) or (tiri_porta_totali >= 5):
                            testo_pulito = analisi_output.replace("<span style='color:#10b981;font-weight:bold;'>", "").replace("</span>", "")
                            messaggio = f"🔥 MILLENIUM ATTACCO IN CORSO 🔥\n\nMatch: {squadra_casa} - {squadra_ospite}\nMinuto: {minuto_corrente}' | Score: {gol_casa}-{gol_ospite}\n\nTiri in Porta: {tiri_porta_totali}\nPressione AP/Min: {ap_al_minuto}\n\nAnalisi Storica:\n{testo_pulito}"
                            invia_telegram(messaggio)
                            DASHBOARD_DATA["alert_inviati_totale"] += 1
                            time.sleep(2)
            DASHBOARD_DATA["match_rilevanti"] = nuovi_match_rilevanti
            salva_dati_su_file()
    except Exception: pass

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
    except Exception: pass

def invia_telegram(messaggio):
    if not TOKEN or not CHAT_ID: return
    try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": messaggio}, timeout=5)
    except Exception: pass

if __name__ == "__main__":
    Thread(target=avvia_server, daemon=True).start()
    print("Millenium Bot Pronto e Attivo!", flush=True)
    while True:
        scansione_partite_live()
        scansione_prematch()
        time.sleep(60)
