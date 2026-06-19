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
    
    html = "<div style='max-height: 380px; overflow-y: auto; border-radius: 8px; border: 1px solid #e2e8f0; background: #ffffff;'>"
    html += "<table style='margin-bottom:0; box-shadow: none; border-radius: 0;'><thead><tr><th>Stato</th><th>Competizione</th><th>File</th></tr></thead><tbody>"
    for nome, codice in DIZIONARIO_CAMPIONATI.items():
        pulito = nome.replace("Calcio. ", "")
        
        if nome in campionati_attivi:
            stato = "<span class='sof-live-badge'>LIVE</span>"
            stile_testo = "color: #3b82f6; font-weight: 600;"
        else:
            stato = "<span style='color:#64748b; font-size:12px;'>Disponibile</span>"
            stile_testo = "color: #1e293b;"
            
        html += f"<tr><td>{stato}</td><td style='font-size:12px; {stile_testo}'>{pulito}</td><td><span class='sof-odds-box'>{codice}.csv</span></td></tr>"
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
            
            res = "<html><head><meta charset='utf-8'><title>Sofascore Style - Millenium</title>"
            res += "<style>"
            # PALETTE SOFASCORE: Sfondo chiaro, testo scuro ed elegante, tocchi blu e verdi
            res += "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #1e293b; margin: 0; padding: 0; }"
            
            # NAVBAR SUPERIORE TIPICA DI SOFASCORE
            res += ".sof-header { background-color: #1b2c4a; color: #ffffff; padding: 14px 20px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }"
            res += ".sof-header h1 { margin: 0; font-size: 20px; font-weight: 700; letter-spacing: -0.5px; display: flex; align-items: center; }"
            res += ".sof-header h1 span { color: #3b82f6; margin-right: 5px; }"
            res += ".sof-header .status-indicator { background: #10b981; color: white; font-size: 11px; padding: 3px 8px; border-radius: 12px; font-weight: 600; }"
            
            res += ".container { max-width: 1250px; margin: 20px auto; padding: 0 15px; }"
            res += ".layout-main { display: grid; grid-template-columns: 1fr 360px; gap: 20px; }"
            res += "@media (max-width: 950px) { .layout-main { grid-template-columns: 1fr; } }"
            
            # MINI STRISCIA STATISTICHE
            res += ".stats-row { display: flex; gap: 15px; margin-bottom: 20px; overflow-x: auto; }"
            res += ".sof-stat-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 16px; min-width: 180px; flex: 1; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }"
            res += ".sof-stat-card h3 { margin: 0 0 4px 0; color: #64748b; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }"
            res += ".sof-stat-card .value { font-size: 18px; font-weight: 700; color: #0f172a; }"
            
            # CONTENITORI PRINCIPALI SEZIONI
            res += ".section-header { background: #ffffff; border: 1px solid #e2e8f0; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; padding: 14px 16px; display: flex; align-items: center; justify-content: space-between; margin-top: 10px; }"
            res += ".section-title { font-size: 15px; font-weight: 700; color: #1e293b; display: flex; align-items: center; gap: 8px; }"
            
            # BARRA DI RICERCA SOFASCORE STYLE
            res += ".sof-search { background: #f1f5f9; border: 1px solid #cbd5e1; color: #334155; border-radius: 6px; padding: 6px 12px; font-size: 13px; outline: none; width: 200px; transition: all 0.2s; }"
            res += ".sof-search:focus { background: #ffffff; border-color: #3b82f6; width: 240px; box-shadow: 0 0 0 3px rgba(59,130,246,0.15); }"
            
            # CONTENITORE RIGHE PARTITE (MATCH ROW)
            res += ".match-list { background: #ffffff; border: 1px solid #e2e8f0; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; overflow: hidden; margin-bottom: 25px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }"
            res += ".match-row { display: flex; align-items: center; padding: 12px 16px; border-bottom: 1px solid #f1f5f9; transition: background 0.15s; }"
            res += ".match-row:last-child { border-bottom: none; }"
            res += ".match-row:hover { background-color: #f8fafc; }"
            
            # ELEMENTI DEL MATCH ROW
            res += ".match-time { width: 55px; font-size: 12px; font-weight: 600; color: #64748b; text-align: left; }"
            res += ".match-time.live { color: #ef4444; animation: flash 1.5s infinite; }"
            res += ".match-teams { flex: 1; display: flex; flex-direction: column; gap: 2px; padding-right: 10px; }"
            res += ".team-name { font-size: 14px; color: #1e293b; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }"
            res += ".match-score { display: flex; flex-direction: column; gap: 2px; font-family: monospace; font-size: 14px; font-weight: 700; color: #0f172a; text-align: right; padding-right: 25px; min-width: 25px; }"
            
            # BOX QUOTE / ANALISI ESTERNA
            res += ".sof-odds-container { display: flex; gap: 8px; align-items: center; justify-content: flex-end; min-width: 280px; }"
            res += ".sof-odds-box { background: #f1f5f9; border: 1px solid #e2e8f0; color: #334155; padding: 6px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; text-align: center; min-width: 70px; }"
            res += ".sof-odds-box.tip { background: #e0f2fe; color: #0369a1; border-color: #bae6fd; min-width: 140px; text-align: left; }"
            
            # BADGES E ALTRI UTILI
            res += ".sof-live-badge { background: #ef4444; color: white; font-size: 10px; font-weight: 700; padding: 2px 5px; border-radius: 4px; letter-spacing: 0.3px; }"
            res += "table { width: 100%; border-collapse: collapse; background: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }"
            res += "th { background: #f8fafc; color: #64748b; font-size: 11px; font-weight: 700; text-transform: uppercase; padding: 10px 14px; border-bottom: 1px solid #e2e8f0; text-align: left; }"
            res += "td { padding: 10px 14px; border-bottom: 1px solid #f1f5f9; font-size: 13px; color: #334155; }"
            
            # CALENDARIO COMPATTO
            res += ".cal-box { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }"
            res += ".cal-title { font-weight: 700; color: #1e293b; margin-bottom: 10px; font-size: 13px; text-transform: uppercase; }"
            res += ".cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; }"
            res += ".cal-header-days { font-size: 11px; color: #94a3b8; font-weight: 600; margin-bottom: 6px; }"
            res += ".cal-day { padding: 6px 0; border-radius: 4px; font-size: 12px; font-weight: 600; }"
            res += ".cal-day.regular-day { background: #f8fafc; color: #475569; border: 1px solid #e2e8f0; }"
            res += ".cal-day.today { background: #3b82f6; color: #ffffff; box-shadow: 0 2px 4px rgba(59,130,246,0.3); }"
            
            res += "@keyframes flash { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }"
            res += "</style></head><body>"
            
            # NAVBAR HEADER
            res += "<div class='sof-header'><h1><span>Sofa</span>score Premium</h1><div class='status-indicator'>LIVE ENGINE ACTIVE</div></div>"
            
            res += "<div class='container'>"
            
            # BANNER STATISTICHE CORRENTI
            res += "<div class='stats-row'>"
            res += f"<div class='sof-stat-card'><h3>Ultimo Update</h3><div class='value' style='color:#3b82f6;'>⏱️ {DASHBOARD_DATA['ultimo_aggiornamento']}</div></div>"
            res += f"<div class='sof-stat-card'><h3>In Scansione</h3><div class='value'>{DASHBOARD_DATA['partite_scansionate']} <span style='font-size:12px;font-weight:normal;color:#64748b;'>match</span></div></div>"
            res += f"<div class='sof-stat-card'><h3>Notifiche Push</h3><div class='value' style='color:#10b981;'>🚀 {DASHBOARD_DATA['alert_inviati_totale']}</div></div>"
            res += "</div>"
            
            # TIMELINE PRINCIPALE
            res += "<div class='layout-main'>"
            res += "<div class='col-left'>"
            
            # BLOCCO DELLE PARTITE IN DIRETTA (LIVE)
            res += "<div class='section-header'><div class='section-title'>⚽ Risultati in Diretta (Live)</div><input type='text' class='sof-search' id='searchLive' placeholder='Cerca partita live...' onkeyup='filterSofList(\"searchLive\", \"liveList\")'></div>"
            res += "<div class='match-list' id='liveList'>"
            if not DASHBOARD_DATA["match_rilevanti"]:
                res += "<div style='padding:30px; color:#64748b; text-align:center; font-size:13px; font-style:italic; background:#ffffff;'>Nessun match live soddisfa i parametri AP/Tiri impostati.</div>"
            else:
                for m in DASHBOARD_DATA["match_rilevanti"]:
                    squadre = m['partita'].split(" - ")
                    casa = squadre[0] if len(squadre) > 0 else "Casa"
                    ospite = squadre[1] if len(squadre) > 1 else "Ospite"
                    
                    punti = m['punteggio'].split(" - ")
                    punti_casa = punti[0] if len(punti) > 0 else "0"
                    punti_ospite = punti[1] if len(punti) > 1 else "0"
                    
                    res += f"<div class='match-row'>"
                    res += f"  <div class='match-time live'>{m['orario']}</div>"
                    res += f"  <div class='match-teams'>"
                    res += f"    <div class='team-name'><b>{casa}</b></div>"
                    res += f"    <div class='team-name'><b>{ospite}</b></div>"
                    res += f"    <div style='font-size:11px; color:#94a3b8; margin-top:2px;'>{m.get('campionato','-')}</div>"
                    res += f"  </div>"
                    res += f"  <div class='match-score'>"
                    res += f"    <div style='color:#ef4444;'>{punti_casa}</div>"
                    res += f"    <div style='color:#ef4444;'>{punti_ospite}</div>"
                    res += f"  </div>"
                    res += f"  <div class='sof-odds-container'>"
                    res += f"    <div class='sof-odds-box tip'>{m['analisi']}</div>"
                    res += f"  </div>"
                    res += f"</div>"
            res += "</div>"
            
            # BLOCCO DEL PALINSESTO FUTURO (PREMATCH)
            res += "<div class='section-header'><div class='section-title'>📅 Programma dei Prossimi Match</div><input type='text' class='sof-search' id='searchPrematch' placeholder='Cerca palinsesto...' onkeyup='filterSofList(\"searchPrematch\", \"prematchList\")'></div>"
            res += "<div class='match-list' id='prematchList'>"
            if not DASHBOARD_DATA.get("match_futuri"):
                res += "<div style='padding:30px; color:#64748b; text-align:center; font-size:13px; font-style:italic; background:#ffffff;'>Nessun match futuro in palinsesto nelle prossime ore.</div>"
            else:
                for mf in DASHBOARD_DATA["match_futuri"]:
                    squadre_f = mf['partita'].split(" - ")
                    casa_f = squadre_f[0] if len(squadre_f) > 0 else "Casa"
                    ospite_f = squadre_f[1] if len(squadre_f) > 1 else "Ospite"
                    
                    res += f"<div class='match-row'>"
                    res += f"  <div class='match-time' style='font-size:11px; line-height:1.2; color:#3b82f6;'>{mf['data_ora']}</div>"
                    res += f"  <div class='match-teams'>"
                    res += f"    <div class='team-name'>{casa_f}</div>"
                    res += f"    <div class='team-name'>{ospite_f}</div>"
                    res += f"    <div style='font-size:11px; color:#94a3b8; margin-top:2px;'>{mf['campionato']}</div>"
                    res += f"  </div>"
                    res += f"  <div class='sof-odds-container'>"
                    res += f"    <div class='sof-odds-box tip' style='background:#f8fafc; color:#475569; border-color:#e2e8f0;'>{mf['analisi']}</div>"
                    res += f"  </div>"
                    res += f"</div>"
            res += "</div>"
            
            res += "</div>"
            
            # COLONNA LATERALE DESTRA (CALENDARIO + LEGA ARCHIVIO)
            res += "<div class='col-right'>"
            res += "<div class='section-header' style='margin-top:0; border-radius:8px 8px 0 0;'><div class='section-title'>🗓️ Calendario Operativo</div></div>"
            res += genera_html_calendario()
            
            res += "<div class='section-header' style='border-radius:8px 8px 0 0; margin-top:20px;'><div class='section-title'>🗄️ Database Storici (.CSV)</div></div>"
            res += genera_html_archivio()
            res += "</div>"
            
            res += "</div></div>"
            
            # FILTRO DINAMICO FLUIDO ADATTO AL NUOVO LAYOUT A LISTA (SOFASCORE STYLE)
            res += "<script>"
            res += "function filterSofList(inputId, listId) {"
            res += "  var input = document.getElementById(inputId);"
            res += "  var filter = input.value.toUpperCase();"
            res += "  var container = document.getElementById(listId);"
            res += "  if(!container) return;"
            res += "  var rows = container.getElementsByClassName('match-row');"
            res += "  for (var i = 0; i < rows.length; i++) {"
            res += "    var text = rows[i].textContent || rows[i].innerText;"
            res += "    if (text.toUpperCase().indexOf(filter) > -1) {"
            res += "      rows[i].style.display = 'flex';"
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
        output = f"📊 {somma_medie:.2f} (C:{media_casa:.1f} F:{media_fuori:.1f}) | "
        if is_live and minuto is not None:
            if somma_medie >= 2.40:
                if minuto <= 35: output += "<b style='color:#10b981;'>💥 OVER 0.5 HT</b>"
                elif minuto <= 65: output += f"<b style='color:#10b981;'>💥 OVER {gol_totali + 1.5}</b>"
                elif minuto <= 82: output += f"<b style='color:#10b981;'>💥 OVER {gol_totali + 0.5}</b>"
                else: output += "No Bet"
            else: output += "No Bet (Storico basso)"
        else:
            if somma_medie >= 3.20: output += "<b>🔍 OVER 2.5</b>"
            elif somma_medie >= 2.40: output += "<b>🔍 OVER 1.5</b>"
            else: output += "<b>🔍 UNDER</b>"
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
                            testo_pulito = analisi_output.replace("<b style='color:#10b981;'>", "").replace("</b>", "").replace("<b>", "").replace("</b>", "")
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
                        "campionato": campeonato, "analisi": analizza_e_consiglia(nome_file_csv, squadra_casa, squadra_ospite, is_live=False)
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
