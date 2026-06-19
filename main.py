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
    except Exception:
        pass

def genera_html_calendario():
    oggi = datetime.now()
    anno = oggi.year
    mese = oggi.month
    giorno_oggi = oggi.day
    nomi_mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    cal = calendar.monthcalendar(anno, mese)
    
    html = f"<div class='cal-box'><div class='cal-title'>📅 {nomi_mesi[mese-1].upper()} {anno}</div><div class='cal-grid cal-header-days'>"
    for d in ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]:
        html += f"<div>{d}</div>"
    html += "</div>"
    for week in cal:
        html += "<div class='cal-grid'>"
        for day in week:
            if day == 0: html += "<div class='cal-day empty'></div>"
            elif day == giorno_oggi: html += f"<div class='cal-day today'>{day}</div>"
            else: html += f"<div class='cal-day regular-day'>{day}</div>"
        html += "</div>"
    html += "</div>"
    return html

def genera_html_archivio():
    campionati_attivi = [m.get("campionato", "") for m in DASHBOARD_DATA.get("match_rilevanti", [])]
    html = "<div style='max-height: 380px; overflow-y: auto; border-radius: 8px; border: 1px solid #cbd5e1; background: #e2e8f0;'><table style='margin-bottom:0; box-shadow: none; border-radius: 0;'><thead><tr><th>Stato</th><th>Competizione</th><th>File</th></tr></thead><tbody>"
    for nome, codice in DIZIONARIO_CAMPIONATI.items():
        pulito = nome.replace("Calcio. ", "")
        stato = "<span class='sof-live-badge'>LIVE</span>" if nome in campionati_attivi else "<span style='color:#475569; font-size:12px;'>Pronto</span>"
        stile_testo = "color: #2563eb; font-weight: 700;" if nome in campionati_attivi else "color: #1e293b;"
        html += f"<tr><td>{stato}</td><td style='font-size:12px; {stile_testo}'>{pulito}</td><td><span class='sof-badge-file'>{codice}.csv</span></td></tr>"
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
            
            # BLOCCO CSS COMPATTO SENZA CONCATENAZIONI PER EVITARE SYNTAXERROR
            html_template = """<html><head><meta charset='utf-8'><title>Millenium Bot Pro</title>
            <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #cbd5e1; color: #1e293b; margin: 0; padding: 0; }
            .sof-header { background-color: #0f172a; color: #ffffff; padding: 15px 25px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }
            .sof-header h1 { margin: 0; font-size: 22px; font-weight: 800; letter-spacing: -0.5px; }
            .sof-header h1 span { color: #3b82f6; }
            .sof-header .engine-badge { background: #10b981; color: white; font-size: 11px; padding: 4px 10px; border-radius: 20px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
            .container { max-width: 1250px; margin: 25px auto; padding: 0 15px; }
            .layout-main { display: grid; grid-template-columns: 1fr 360px; gap: 24px; }
            @media (max-width: 950px) { .layout-main { grid-template-columns: 1fr; } }
            .stats-row { display: flex; gap: 15px; margin-bottom: 25px; }
            .sof-stat-card { background: #e2e8f0; border-radius: 10px; padding: 15px 20px; flex: 1; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid #cbd5e1; }
            .sof-stat-card h3 { margin: 0 0 5px 0; color: #475569; font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 700; }
            .sof-stat-card .value { font-size: 20px; font-weight: 800; color: #0f172a; }
            .section-header { background: #e2e8f0; border: 1px solid #cbd5e1; border-bottom: 2px solid #cbd5e1; border-top-left-radius: 10px; border-top-right-radius: 10px; padding: 16px 20px; display: flex; align-items: center; justify-content: space-between; }
            .section-title { font-size: 16px; font-weight: 700; color: #1e293b; display: flex; align-items: center; gap: 8px; }
            .sof-search { background: #d97706; border: 1px solid #b45309; color: #ffffff; border-radius: 20px; padding: 7px 16px; font-size: 13px; outline: none; width: 210px; font-weight: 600; transition: all 0.2s ease; }
            .sof-search::placeholder { color: rgba(255, 255, 255, 0.85); }
            .sof-search:focus { background: #b45309; border-color: #78350f; width: 250px; box-shadow: 0 0 0 3px rgba(217,119,6,0.3); }
            .match-list { background: #e2e8f0; border: 1px solid #cbd5e1; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px; overflow: hidden; margin-bottom: 30px; box-shadow: 0 1px 4px rgba(0,0,0,0.03); }
            .match-row { display: flex; align-items: center; padding: 16px 20px; border-bottom: 1px solid #cbd5e1; transition: background 0.15s; }
            .match-row:last-child { border-bottom: none; }
            .match-row:hover { background-color: #cbd5e1; }
            .match-time-block { width: 65px; display: flex; flex-direction: column; align-items: flex-start; justify-content: center; font-size: 13px; font-weight: 700; color: #475569; }
            .match-time-block.live { color: #ef4444; animation: blinker 1.5s linear infinite; }
            .match-teams-block { flex: 1; display: flex; flex-direction: column; gap: 6px; padding-left: 10px; border-left: 1px solid #cbd5e1; }
            .team-row { font-size: 14px; font-weight: 600; color: #1e293b; display: flex; align-items: center; justify-content: space-between; }
            .league-subtitle { font-size: 11px; color: #64748b; font-weight: 500; margin-top: 2px; text-transform: uppercase; letter-spacing: 0.3px; }
            .match-scores-block { display: flex; flex-direction: column; gap: 6px; font-size: 14px; font-weight: 700; color: #0f172a; text-align: center; padding: 0 25px 0 15px; border-right: 1px solid #cbd5e1; min-width: 30px; }
            .score-value { color: #ef4444; font-family: monospace; font-size: 15px; }
            .match-analysis-block { min-width: 340px; padding-left: 20px; display: flex; align-items: center; justify-content: flex-end; }
            .sof-quote-box { background: #dcfce7; border: 1px solid #bbf7d0; color: #166534; padding: 8px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; width: 100%; text-align: left; box-shadow: 0 1px 2px rgba(0,0,0,0.02); }
            .sof-quote-box.prematch { background: #cbd5e1; border-color: #cbd5e1; color: #334155; }
            .sof-live-badge { background: #ef4444; color: white; font-size: 10px; font-weight: 800; padding: 2px 6px; border-radius: 4px; display: inline-block; margin-bottom: 2px; }
            .sof-badge-file { background: #cbd5e1; border: 1px solid #cbd5e1; color: #334155; padding: 4px 8px; border-radius: 6px; font-weight: 600; font-size: 11px; }
            table { width: 100%; border-collapse: collapse; background: #e2e8f0; }
            th { background: #cbd5e1; color: #1e293b; font-size: 11px; font-weight: 700; text-transform: uppercase; padding: 12px 16px; border-bottom: 1px solid #cbd5e1; text-align: left; }
            td { padding: 12px 16px; border-bottom: 1px solid #cbd5e1; font-size: 13px; color: #1e293b; }
            .cal-box { background: #e2e8f0; border: 1px solid #cbd5e1; border-radius: 10px; padding: 16px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
            .cal-title { font-weight: 700; color: #1e293b; margin-bottom: 12px; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }
            .cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; }
            .cal-header-days { font-size: 11px; color: #475569; font-weight: 700; margin-bottom: 8px; text-transform: uppercase; }
            .cal-day { padding: 7px 0; border-radius: 4px; font-size: 12px; font-weight: 600; }
            .cal-day.regular-day { background: #f8fafc; color: #1e293b; border: 1px solid #cbd5e1; }
            .cal-day.today { background: #3b82f6; color: #ffffff; box-shadow: 0 2px 6px rgba(59,130,246,0.3); }
            @keyframes blinker { 50% { opacity: 0.4; } }
            </style></head><body>
            <div class='sof-header'><h1><span>Millenium</span> Bot</h1><div class='engine-badge'>Live Core Analisi V3</div></div>
            <div class='container'>
            <div class='stats-row'>
                <div class='sof-stat-card'><h3>Ultimo Controllo Flusso</h3><div class='value' style='color:#3b82f6;'>⏱️ {ultimo_aggiornamento}</div></div>
                <div class='sof-stat-card'><h3>Match Analizzati 1X</h3><div class='value'>{partite_scansionate} <span style='font-size:12px;color:#475569;font-weight:normal;'>attivi</span></div></div>
                <div class='sof-stat-card'><h3>Notifiche Push Inviate</h3><div class='value' style='color:#10b981;'>🚀 {alert_inviati_totale}</div></div>
            </div>
            <div class='layout-main'>
            <div class='col-left'>
            <div class='section-header'><div class='section-title'>⚽ Risultati in Diretta (Live)</div><input type='text' class='sof-search' id='searchLive' placeholder='Cerca live...' onkeyup='filterSofRows("searchLive", "liveList")'></div>
            <div class='match-list' id='liveList'>
            """
            
            # Popolamento dinamico Live
            if not DASHBOARD_DATA["match_rilevanti"]:
                html_template += "<div style='padding:40px; color:#475569; text-align:center; font-size:13px; font-style:italic; background:#e2e8f0;'>Nessun match attivo soddisfa i filtri AP/Tiri impostati.</div>"
            else:
                for m in DASHBOARD_DATA["match_rilevanti"]:
                    squadre = m['partita'].split(" - ")
                    casa = squadre[0] if len(squadre) > 0 else "Team Casa"
                    ospite = squadre[1] if len(squadre) > 1 else "Team Ospite"
                    punti = m['punteggio'].split(" - ")
                    punti_casa = punti[0] if len(punti) > 0 else "0"
                    punti_ospite = punti[1] if len(punti) > 1 else "0"
                    
                    html_template += f"""
                    <div class='match-row'>
                      <div class='match-time-block live'><span class='sof-live-badge'>LIVE</span>{m['orario']}</div>
                      <div class='match-teams-block'>
                        <div class='team-row'><span>{casa}</span></div>
                        <div class='team-row'><span>{ospite}</span></div>
                        <div class='league-subtitle'>{m.get('campionato','-')}</div>
                      </div>
                      <div class='match-scores-block'>
                        <div class='score-value'>{punti_casa}</div>
                        <div class='score-value'>{punti_ospite}</div>
                      </div>
                      <div class='match-analysis-block'>
                        <div class='sof-quote-box'>{m['analisi']}</div>
                      </div>
                    </div>"""
                    
            html_template += "</div><div class='section-header'><div class='section-title'>📅 Palinsesto Prossimi Match</div><input type='text' class='sof-search' id='searchPrematch' placeholder='Cerca palinsesto...' onkeyup='filterSofRows(\"searchPrematch\", \"prematchList\")'></div><div class='match-list' id='prematchList'>"
            
            # Popolamento dinamico Prematch
            if not DASHBOARD_DATA.get("match_futuri"):
                html_template += "<div style='padding:40px; color:#475569; text-align:center; font-size:13px; font-style:italic; background:#e2e8f0;'>Palinsesto prematch vuoto o mercati chiusi temporaneamente.</div>"
            else:
                for mf in DASHBOARD_DATA["match_futuri"]:
                    squadre_f = mf['partita'].split(" - ")
                    casa_f = squadre_f[0] if len(squadre_f) > 0 else "Team Casa"
                    ospite_f = squadre_f[1] if len(squadre_f) > 1 else "Team Ospite"
                    
                    html_template += f"""
                    <div class='match-row'>
                      <div class='match-time-block' style='color:#3b82f6; font-size:11px;'>{mf['data_ora']}</div>
                      <div class='match-teams-block'>
                        <div class='team-row'><span>{casa_f}</span></div>
                        <div class='team-row'><span>{ospite_f}</span></div>
                        <div class='league-subtitle'>{mf['campionato']}</div>
                      </div>
                      <div class='match-scores-block' style='border-right:none; color:#64748b;'>VS</div>
                      <div class='match-analysis-block'>
                        <div class='sof-quote-box prematch'>{mf['analisi']}</div>
                      </div>
                    </div>"""
                    
            # Chiusura Layout Destro e Script
            html_template += f"""
            </div></div>
            <div class='col-right'>
            <div class='section-header' style='margin-top:0; border-radius:10px 10px 0 0;'><div class='section-title'>🗓️ Calendario Operativo</div></div>
            {genera_html_calendario()}
            <div class='section-header' style='border-radius:10px 10px 0 0; margin-top:25px;'><div class='section-title'>🗄️ Database Storici (.CSV)</div></div>
            {genera_html_archivio()}
            </div></div></div>
            <script>
            function filterSofRows(inputId, listId) {{
              var input = document.getElementById(inputId);
              var filter = input.value.toUpperCase();
              var container = document.getElementById(listId);
              if(!container) return;
              var rows = container.getElementsByClassName('match-row');
              for (var i = 0; i < rows.length; i++) {{
                var text = rows[i].textContent || rows[i].innerText;
                if (text.toUpperCase().indexOf(filter) > -1) {{
                  rows[i].style.display = 'flex';
                }} else {{
                  rows[i].style.display = 'none';
                }}
              }}
            }}
            setTimeout(function(){{ location.reload(); }}, 15000);
            </script></body></html>
            """
            
            output_finalizzato = html_template.format(
                ultimo_aggiornamento=DASHBOARD_DATA['ultimo_aggiornamento'],
                partite_scansionate=DASHBOARD_DATA['partite_scansionate'],
                alert_inviati_totale=DASHBOARD_DATA['alert_inviati_totale']
            )
            self.wfile.write(output_finalizzato.encode("utf-8"))
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
    if not os.path.exists(nome_file): return "Nessun CSV trovato."
    try:
        df = pd.read_csv(nome_file)
        partite_casa = df[df['HomeTeam'].str.contains(casa_live, case=False, na=False)]
        partite_ospite = df[df['AwayTeam'].str.contains(ospite_live, case=False, na=False)]
        media_casa = float(partite_casa['FTHG'].mean()) if not partite_casa.empty and 'FTHG' in df.columns else 0.0
        media_fuori = float(partite_ospite['FTAG'].mean()) if not partite_ospite.empty and 'FTAG' in df.columns else 0.0
        somma_medie = media_casa + media_fuori
        output = f"📊 Media: {somma_medie:.2f} (C:{media_casa:.1f} F:{media_fuori:.1f}) | "
        if is_live and minuto is not None:
            if somma_medie >= 2.40:
                if minuto <= 35: output += "<b style='color:#166534;'>💥 OVER 0.5 HT</b>"
                elif minuto <= 65: output += f"<b style='color:#166534;'>💥 OVER {gol_totali + 1.5}</b>"
                elif minuto <= 82: output += f"<b style='color:#166534;'>💥 OVER {gol_totali + 0.5}</b>"
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
                            testo_pulito = analisi_output.replace("<b style='color:#166534;'>", "").replace("</b>", "").replace("<b>", "").replace("</b>", "")
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
    try: requests.post(f"https://api.telegram
