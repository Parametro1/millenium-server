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
            
            badge_campionati = "".join([f"<span class='db-league-badge'>{sigla}</span>" for sigla in CAMPIONATI_ALL])
            righe_campionati_html = "".join([f"<tr><td style='color:#58a6ff; font-weight:700; border-bottom: 1px solid #161b22;'>{sigla}</td><td style='color:#8b949e; border-bottom: 1px solid #161b22;'>{nome}</td></tr>" for nome, sigla in DIZIONARIO_CAMPIONATI.items()])

            giorni_list = []
            nomi_giorni = ["Dom", "Lun", "Mar", "Mer", "Gio", "Ven", "Sab"]
            oggi = datetime.now()
            for i in range(7):
                d = oggi + timedelta(days=i)
                tag = "OGGI" if i == 0 else ("DOMANI" if i == 1 else f"{nomi_giorni[d.weekday()]} {d.strftime('%d/%m')}")
                giorni_list.append({"id": d.strftime("%d/%m"), "label": tag, "is_oggi": i == 0})
            
            giorni_json = json.dumps(giorni_list)

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Millenium — Professional Trading Terminal</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #010409; color: #c9d1d9; margin:0; padding:25px; box-sizing: border-box; }}
                    .container {{ max-width: 1700px; margin: 0 auto; }}
                    
                    /* HEADER STYLE CONTEMPORANEO */
                    .header {{ background: #0d1117; padding: 20px 30px; border-radius: 12px; border: 1px solid #21262d; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; }}
                    h1 {{ color: #f0f6fc; margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.5px; display: flex; align-items: center; gap: 10px; }}
                    .status-bar {{ display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }}
                    
                    .badge {{ background: #161b22; color: #8b949e; padding: 8px 14px; border-radius: 6px; border: 1px solid #30363d; font-size: 13px; font-weight: 600; }}
                    .badge span {{ color: #58a6ff; font-weight: 700; }}
                    .badge-online {{ background: rgba(46, 160, 67, 0.15); color: #3fb950; border-color: rgba(56, 139, 253, 0.15); }}
                    .badge-live-count {{ background: rgba(248, 81, 73, 0.1); color: #f85149; border-color: rgba(248, 81, 73, 0.2); }}

                    /* CONTROLS & DATABASE BADGES */
                    .controls-panel {{ background: #0d1117; border: 1px solid #21262d; padding: 20px; border-radius: 12px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; gap: 20px; flex-wrap: wrap; }}
                    .search-box {{ background: #010409; border: 1px solid #30363d; color: #f0f6fc; padding: 10px 16px; border-radius: 6px; font-size: 14px; width: 320px; transition: border-color 0.2s; }}
                    .search-box:focus {{ outline: none; border-color: #58a6ff; }}
                    
                    .db-info {{ display: flex; flex-direction: column; gap: 8px; flex: 1; max-width: 70%; }}
                    .db-title {{ font-size: 11px; color: #8b949e; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }}
                    .badge-container {{ display: flex; gap: 6px; flex-wrap: wrap; }}
                    .db-league-badge {{ background: #161b22; color: #c9d1d9; font-weight: 600; font-size: 11px; padding: 4px 8px; border-radius: 4px; border: 1px solid #30363d; }}

                    /* CALENDARIO ULTRA-CLEAN */
                    .calendar-section {{ background: #0d1117; border: 1px solid #21262d; padding: 20px; border-radius: 12px; margin-bottom: 25px; }}
                    .calendar-title {{ font-size: 12px; font-weight: 700; text-transform: uppercase; color: #d29922; margin-bottom: 15px; letter-spacing: 0.5px; }}
                    .calendar-grid {{ display: flex; gap: 10px; flex-wrap: wrap; }}
                    
                    .cal-btn {{ flex: 1; min-width: 125px; padding: 12px 8px; border-radius: 6px; border: 1px solid #21262d; background: #161b22; text-align: center; cursor: pointer; font-weight: 600; font-size: 13px; transition: all 0.2s ease; }}
                    .cal-btn .cal-sub {{ font-size: 11px; font-weight: 500; margin-top: 3px; display: block; }}
                    
                    /* Stati condizionali del calendario */
                    .cal-btn.cal-oggi {{ background: #0e2a1f !important; color: #46df70 !important; border-color: #2ea043 !important; }}
                    .cal-btn.cal-oggi .cal-sub {{ color: #46df70 !important; opacity: 0.8; }}
                    
                    .cal-btn.cal-futuro {{ color: #d29922 !important; }}
                    .cal-btn.cal-futuro .cal-sub {{ color: #d29922 !important; opacity: 0.8; }}
                    
                    .cal-btn.cal-hot {{ border-color: #ab7df6; background: rgba(143, 90, 241, 0.05); }}
                    .cal-btn.cal-normal {{ border-color: #30363d; }}
                    .cal-btn.cal-empty {{ background: #0d1117; border-color: #21262d; opacity: 0.4; cursor: not-allowed; color: #8b949e !important; }}
                    .cal-btn.cal-empty .cal-sub {{ color: #8b949e !important; }}
                    
                    .cal-btn.cal-selected:not(.cal-oggi) {{ background: #d29922 !important; color: #010409 !important; border-color: #f0e6d2 !important; }}
                    .cal-btn.cal-selected:not(.cal-oggi) .cal-sub {{ color: #010409 !important; }}

                    /* GRID E PANNELLI TERMINAL */
                    .dashboard-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px; }}
                    @media (max-width: 1350px) {{ .dashboard-grid {{ grid-template-columns: 1fr; }} }}
                    
                    .panel {{ background: #0d1117; border-radius: 12px; padding: 20px; border: 1px solid #21262d; }}
                    .panel-live {{ border-top: 3px solid #f85149; }}
                    .panel-future {{ border-top: 3px solid #d29922; }}
                    .panel-leagues {{ border: 1px solid #21262d; background: #0d1117; }}
                    
                    h2 {{ font-size: 15px; font-weight: 600; margin-top: 0; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #21262d; display: flex; align-items: center; gap: 8px; }}
                    .live-title {{ color: #f85149; }} .future-title {{ color: #d29922; }} .leagues-title {{ color: #58a6ff; }}
                    
                    /* RE-DESIGN STRUTTURA TABELLE */
                    table {{ width: 100%; border-collapse: collapse; }}
                    th {{ color: #8b949e; text-align: left; padding: 12px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid #21262d; }}
                    td {{ padding: 14px 12px; border-bottom: 1px solid #21262d; vertical-align: top; font-size: 13.5px; }}
                    tr.searchable-row:hover td {{ background-color: #161b22; }}
                    
                    .time-badge {{ background: #21262d; color: #c9d1d9; padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 12px; border: 1px solid #30363d; display: inline-block; }}
                    .time-badge.future {{ border-color: rgba(210, 153, 34, 0.3); color: #d29922; background: rgba(210, 153, 34, 0.05); }}
                    
                    .match-team {{ font-weight: 600; font-size: 15px; color: #f0f6fc; margin-bottom: 4px; }}
                    .score-badge {{ font-size: 12px; color: #ff7b72; background: rgba(248, 81, 73, 0.1); padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(248, 81, 73, 0.2); display: inline-block; font-weight: 600; }}
                    .league-text {{ font-size: 11px; color: #8b949e; margin-top: 4px; font-weight: 500; }}
                    
                    /* BADGES STATISTICHE LIVE COERENTI */
                    .live-stat-box {{ display: flex; flex-direction: column; gap: 4px; align-items: center; min-width: 90px; }}
                    .pill-stat {{ background: rgba(56, 139, 253, 0.1); color: #58a6ff; border: 1px solid rgba(56, 139, 253, 0.2); padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: 700; font-family: monospace; text-align: center; width: 80%; }}
                    .pill-stat.ap {{ background: rgba(139, 92, 246, 0.1); color: #a78bfa; border-color: rgba(139, 92, 246, 0.2); font-weight: 500; font-size: 11px; }}
                    
                    .analysis-cell {{ font-size: 13px; color: #c9d1d9; line-height: 1.5; white-space: pre-line; background: #161b22; padding: 12px; border-radius: 6px; border: 1px solid #30363d; }}
                    .state-row-message {{ text-align: center; color: #8b949e; padding: 40px; font-style: italic; font-size: 13px; }}
                    b {{ color: #58a6ff; font-weight: 600; }} i {{ color: #8b949e; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>⚡ Millenium Intelligence Terminal</h1>
                        <div class="status-bar">
                            <div class="badge badge-online">🟢 Radar Connected</div>
                            <div class="badge badge-live-count">Live: <span id="count-scanned">0</span></div>
                            <div class="badge">Alerts: <span id="count-alerts">0</span></div>
                            <div class="badge">Aggiornato: <span id="time-updated">Mai</span></div>
                        </div>
                    </div>
                    
                    <div class="controls-panel">
                        <input type="text" id="searchBar" class="search-box" placeholder="Filtra squadre o campionati..." onkeyup="filterTables()">
                        <div class="db-info">
                            <span class="db-title">🗄️ Database Archivi Attivi ({len(CAMPIONATI_ALL)}):</span>
                            <div class="badge-container">{badge_campionati}</div>
                        </div>
                    </div>

                    <div class="calendar-section">
                        <div class="calendar-title">📅 CALENDARIO OPERATIVO SETTIMANALE</div>
                        <div class="calendar-grid" id="calendarContainer"></div>
                    </div>
                    
                    <div class="dashboard-grid">
                        <div class="panel panel-live">
                            <h2 class="live-title">🔴 Real-Time Live Stream</h2>
                            <table>
                                <thead>
                                    <tr>
                                        <th style="width: 12%; text-align:center;">Minuto</th>
                                        <th style="width: 48%;">Incontro / Competizione</th>
                                        <th style="width: 18%; text-align:center;">Metriche Live</th>
                                        <th style="width: 22%;">Suggerimento</th>
                                    </tr>
                                </thead>
                                <tbody id="live-tbody">
                                    <tr><td colspan='4' class="state-row-message">Sincronizzazione flussi live in corso...</td></tr>
                                </tbody>
                            </table>
                        </div>
                        
                        <div class="panel panel-future">
                            <h2 class="future-title">⏳ Palinsesto Prossime Ore</h2>
                            <table>
                                <thead>
                                    <tr>
                                        <th style="width: 18%; text-align:center;">Inizio</th>
                                        <th style="width: 52%;">Match / Campionato</th>
                                        <th style="width: 30%;">Analisi Statistica</th>
                                    </tr>
                                </thead>
                                <tbody id="future-tbody">
                                    <tr><td colspan='3' class="state-row-message">Sincronizzazione palinsesto in corso...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div class="panel panel-leagues">
                        <h2 class="leagues-title">📋 Mapping Database / Legenda Campionati</h2>
                        <table style="margin-top:5px;">
                            <thead>
                                <tr>
                                    <th style="width: 15%;">Codice Archivio</th>
                                    <th style="width: 85%;">Stringa Origine 1xBet</th>
                                </tr>
                            </thead>
                            <tbody>
                                {righe_campionati_html}
                            </tbody>
                        </table>
                    </div>
                </div>

                <script>
                    const giorniSettimana = {giorni_json};
                    let giornoSelezionato = giorniSettimana[0].id;
                    let cacheMatchFuturi = [];

                    function renderCalendario(matchFuturi) {{
                        const container = document.getElementById('calendarContainer');
                        container.innerHTML = "";
                        giorniSettimana.forEach(g => {{
                            let count = matchFuturi.filter(m => m.data_ora.includes(g.id)).length;
                            let classeStato = "cal-empty";
                            let subText = "No Match";
                            if (count > 0) {{
                                subText = count === 1 ? "1 Match" : `${{count}} Match`;
                                classeStato = count >= 5 ? "cal-hot" : "cal-normal";
                            }}
                            let classeTipogiorno = g.is_oggi ? "cal-oggi" : "cal-futuro";
                            let classeSelezionato = (g.id === giornoSelezionato) ? "cal-selected" : "";
                            const btn = document.createElement('div');
                            btn.className = `cal-btn ${{classeTipogiorno}} ${{classeStato}} ${{classeSelezionato}}`;
                            btn.innerHTML = `${{g.label}} <span class="cal-sub">${{subText}}</span>`;
                            if (count > 0 || g.is_oggi) {{
                                btn.onclick = () => {{
                                    giornoSelezionato = g.id;
                                    renderCalcoloPrematch();
                                    renderCalendario(matchFuturi);
                                }};
                            }}
                            container.appendChild(btn);
                        }});
                    }}

                    function renderCalcoloPrematch() {{
                        const futureTbody = document.getElementById('future-tbody');
                        let matchFiltrati = cacheMatchFuturi.filter(m => m.data_ora.includes(giornoSelezionato));
                        if (matchFiltrati.length === 0) {{
                            futureTbody.innerHTML = `<tr><td colspan='3' class="state-row-message">Nessun match programmato per la data selezionata.</td></tr>`;
                        }} else {{
                            let futureHtml = "";
                            matchFiltrati.forEach(mf => {{
                                futureHtml += `
                                    <tr class="searchable-row">
                                        <td style
