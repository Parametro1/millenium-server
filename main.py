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
    "Italia. Serie A": "I1", "Italia. Serie B": "I2",
    "Inghilterra. Premier League": "E0", "Inghilterra. Championship": "E1",
    "Inghilterra. League One": "E2", "Inghilterra. League Two": "E3",
    "Inghilterra. National League": "EC", "Germania. Bundesliga": "D1",
    "Germania. 2. Bundesliga": "D2", "Germania. 3. Liga": "D3",
    "Spagna. Primera Division": "SP1", "Spagna. Segunda Division": "SP2",
    "Francia. Ligue 1": "F1", "Francia. Ligue 2": "F2",
    "Olanda. Eredivisie": "N1", "Olanda. Eerste Divisie": "N2",
    "Portogallo. Primeira Liga": "P1", "Turchia. SuperLig": "T1",
    "Belgio. Pro League": "B1", "Scozia. Premiership": "SC0",
    "Scozia. Championship": "SC1", "Grecia. Super League": "G1",
    "Austria. Bundesliga": "A1", "Svizzera. Super League": "SW1",
    "Danimarca. Superligaen": "DN1", "Norvegia. Eliteserien": "N1",
    "Svezia. Allsvenskan": "S1", "USA. MLS": "USA",
    "Brasile. Serie A": "BRA", "Argentina. Primera Division": "ARG",
    "Giappone. J1 League": "JPN", "Messico. Liga MX": "MEX"
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
    
    html = "<table style='margin-top:10px;'><thead><tr><th>Stato</th><th>Lega</th><th>File</th></tr></thead><tbody>"
    for nome, codice in DIZIONARIO_CAMPIONATI.items():
        pulito = nome.replace("Calcio. ", "")
        
        if nome in campionati_attivi:
            stato = "<span style='animation: pulse 1.5s infinite;'>🔴 LIVE</span>"
            stile_testo = "color: #ef4444; font-weight: bold;"
        else:
            stato = "🟢"
            stile_testo = "color: #cbd5e1;"
            
        html += f"<tr><td>{stato}</td><td style='font-size:12px; {stile_testo}'><b>{pulito}</b></td><td><span class='badge' style='background:#475569;'>{codice}.csv</span></td></tr>"
    html += "</tbody></table>"
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
            
            res = "<html><head><meta charset='utf-8'><title>Millenium Terminal</title>"
            res += "<style>"
            res += "body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0b0f19; color: #e2e8f0; margin: 0; padding: 20px; }"
            res += ".container { max-width: 1200px; margin: 0 auto; }"
            res += "h1 { color: #38bdf8; border-bottom: 2px solid #1e293b; padding-bottom: 10px; margin-bottom: 25px; display: flex; align-items: center; justify-content: space-between; }"
            res += ".layout-main { display: grid; grid-template-columns: 1fr 360px; gap: 30px; }"
            res += "@media (max-width: 900px) { .layout-main { grid-template-columns: 1fr; } }"
            res += ".stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 25px; }"
            res += ".card { background: #111827; border: 1px solid #1e293b; padding: 15px; border-radius: 8px; }"
            res += ".card h3 { margin: 0 0 5px 0; color: #94a3b8; font-size: 12px; text-transform: uppercase; }"
            res += ".card .value { font-size: 20px; font-weight: bold; color: #f8fafc; }"
            res += ".card .highlight { color: #10b981; }"
            res += "h2 { color: #f1f5f9; font-size: 17px; margin-top: 0; margin-bottom: 15px; border-left: 4px solid #38bdf8; padding-left: 10px; text-transform: uppercase; letter-spacing: 0.05em; }"
            res += "table { width: 100%; border-collapse: collapse; background: #111827; border-radius: 8px; overflow: hidden; border: 1px solid #1e293b; margin-bottom: 30px; }"
            res += "th { background: #1e293b; color: #38bdf8; text-align: left; padding: 12px; font-size: 13px; }"
            res += "td { padding: 12px; border-bottom: 1px solid #1e293b; font-size: 13px; color: #cbd5e1; }"
            res += "tr:hover { background: #1f2937; }"
            res += ".badge { background: #0284c7; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; }"
            res += ".badge-live { background: #dc2626; animation: pulse 2s infinite; }"
            
            res += ".cal-box { background: #111827; border: 1px solid #1e293b; border-radius: 8px; padding: 15px; text-align: center; margin-bottom: 25px; }"
            res += ".cal-title { font-weight: bold; color: #38bdf8; margin-bottom: 15px; font-size: 14px; letter-spacing: 0.05em; }"
            res += ".cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; margin-bottom: 5px; }"
            res += ".cal-header-days { font-size: 11px; color: #64748b; font-weight: bold; margin-bottom: 10px; }"
            res += ".cal-day { padding: 8px 0; border-radius: 4px; font-size: 12px; font-family: monospace; font-weight: bold; }"
            res += ".cal-day.empty { background: transparent; }"
            res += ".cal-day.regular-day { background: #1e3a8a; color: #f59e0b; }"
            res += ".cal-day.today { background: #ffffff; color: #10b981; box-shadow: 0 0 10px rgba(255,255,255,0.3); }"
            
            res += "@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }"
            res += "</style></head><body><div class='container'>"
            
            res += "<h1><span>⚡ MILLENIUM TERMINAL</span> <span style='font-size:14px;color:#64748b;'>Sistema Online</span></h1>"
            
            res += "<div class='stats-grid'>"
            res += f"<div class='card'><h3>Ultimo Update</h3><div class='value'>{DASHBOARD_DATA['ultimo_aggiornamento']}</div></div>"
            res += f"<div class='card'><h3>Live Scansionati</h3><div class='value highlight'>{DASHBOARD_DATA['partite_scansionate']}</div></div>"
            res += f"<div class='card'><h3>Alert Telegram</h3><div class='value' style='color:#38bdf8;'>{DASHBOARD_DATA['alert_inviati_totale']}</div></div>"
            res += "</div>"
            
            res += "<div class='layout-main'>"
            res += "<div class='col-left'>"
            
            res += "<h2>🔥 Monitoraggio Live</h2>"
            if not DASHBOARD_DATA["match_rilevanti"]:
                res += "<div style='background:#111827;padding:20px;border-radius:8px;border:1px solid #1e293b;color:#64748b;margin-bottom:30px;'>Nessun match attivo con i parametri minimi richiesti.</div>"
            else:
                res += "<table><thead><tr><th>Tempo</th><th>Incontro</th><th>Score</th><th>Consiglio / Archivio CSV</th></tr></thead><tbody>"
                for m in DASHBOARD_DATA["match_rilevanti"]:
                    res += f"<tr><td><span class='badge badge-live'>{m['orario']}</span></td><td><b>{m['partita']}</b><br><span style='font-size:11px;color:#64748b;'>{m.get('campionato','-')}</span></td><td><span style='font-family:monospace;font-weight:bold;color:#f59e0b;'>{m['punteggio']}</span></td><td>{m['analisi']}</td></tr>"
                res += "</tbody></table>"
            
            res += "<h2>📅 Palinsesto Prossimi Match</h2>"
            if not DASHBOARD_DATA.get("match_futuri"):
                res += "<div style='background:#111827;padding:20px;border-radius:8px;border:1px solid #1e293b;color:#64748b;'>Palinsesto prematch momentaneamente vuoto.</div>"
            else:
                res += "<table><thead><tr><th>Ora</th><th>Incontro</th><th>Campionato</th><th>Analisi Prematch</th></tr></thead><tbody>"
                for mf in DASHBOARD_DATA["match_futuri"]:
                    res += f"<tr><td><span class='badge'>{mf['data_ora']}</span></td><td><b>{mf['partita']}</b></td><td><span style='color:#94a3b8;font-size:11px;'>{mf['campionato']}</span></td><td>{mf['analisi']}</td></tr>"
                res += "</tbody></table>"
                
            res += "</div>"
            
            res += "<div class='col-right'>"
            res += "<h2>&Igrave;📆 Calendario</h2>"
            res += genera_html_calendario()
            
            res += "<h2 style='margin-top:20px;'>🗄️ Campionati in Archivio</h2>"
            res += genera_html_archivio()
            res += "</div>"
            
            res += "</div></div><script>setTimeout(function(){ location.reload(); }, 15000);</script></body></html>"
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
    if not TOKEN or not CHAT_ID: 
        print("DEBUG TELEGRAM: Mancano TOKEN o CHAT_ID!", flush=True)
        return
    try: 
        r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": messaggio}, timeout=5)
        print(f"DEBUG TELEGRAM: Inviato alert. Stato risposta: {r.status_code}", flush=True)
    except Exception as e: 
        print(f"DEBUG TELEGRAM ERRORE: {e}", flush=True)

if __name__ == "__main__":
    Thread(target=avvia_server, daemon=True).start()
    print("Millenium Bot Pronto e Attivo!", flush=True)
    
    # Messaggio di avvio per confermare che l'accoppiamento token/id è perfetto
    invia_telegram("✅ Il motore Millenium è ripartito con il codice completo!")
    
    while True:
        scansione_partite_live()
        scansione_prematch()
        time.sleep(60)
