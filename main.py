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
    "Calcio. Germania. Bundesliga": "D1", "Calcio. Germania. 2. Bundesliga": "D2",
    "Calcio. Italia. Serie A": "I1", "Calcio. Italia. Serie B": "I2",
    "Calcio. Olanda. Eredivisie": "N1", "Calcio. Spagna. Primera Division": "SP1",
    "Calcio. Spagna. Segunda Division": "SP2", "Calcio. Francia. Ligue 1": "F1",
    "Calcio. Francia. Ligue 2": "F2", "Calcio. Turchia. SuperLig": "T1", "Calcio. USA. MLS": "USA"
}

CAMPIONATI_ALL = ["E0", "E1", "D1", "D2", "I1", "I2", "N1", "SP1", "SP2", "F1", "F2", "T1", "USA"]

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
            
            righe_campionati_html = ""
            for nome_esteso, sigla in DIZIONARIO_CAMPIONATI.items():
                righe_campionati_html += f"<tr><td style='color:#388bfd; font-weight:900;'>{sigla}</td><td style='color:#cbd5e1; font-weight:600;'>{nome_esteso}</td></tr>"

            giorni_list = []
            nomi_giorni = ["Dom", "Lun", "Mar", "Mer", "Gio", "Ven", "Sab"]
            oggi = datetime.now()
            for i in range(7):
                d = oggi + timedelta(days=i)
                tag = "OGGI" if i == 0 else ("DOMANI" if i == 1 else f"{nomi_giorni[d.weekday()]} {d.strftime('%d/%m')}")
                giorni_list.append({"id": d.strftime("%d/%m"), "label": tag})
            
            giorni_json = json.dumps(giorni_list)

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Millenium — Trading Intelligence Hub</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: 'Segoe UI', system-ui, sans-serif; background-color: #050811; color: #ffffff; margin:0; padding:20px; }}
                    .container {{ max-width: 1650px; margin: 0 auto; }}
                    
                    .header {{ background: linear-gradient(135deg, #09152e 0%, #111c36 100%); padding: 22px 30px; border-radius: 12px; border: 2px solid #1e366a; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }}
                    h1 {{ color: #ffffff; margin: 0; font-size: 26px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; text-shadow: 0 0 10px rgba(56,139,253,0.4); }}
                    .status-bar {{ display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }}
                    
                    .badge {{ background: #02040a; color: #ffffff; padding: 10px 16px; border-radius: 8px; border: 2px solid #1e366a; font-size: 14px; font-weight: 700; }}
                    .badge span {{ color: #388bfd; font-weight: 900; font-family: monospace; font-size: 15px; }}
                    .badge-online {{ background: #0c2d14; color: #4af262; border-color: #1f6f32; text-shadow: 0 0 8px #4af262; }}
                    .badge-live-count {{ background: #3b0d0d; color: #ff6b6b; border-color: #7a1c1c; }}
                    .badge-live-count span {{ color: #ff6b6b; }}

                    .controls-panel {{ display: flex; justify-content: space-between; align-items: center; background: #091124; border: 2px solid #16264c; padding: 20px; border-radius: 12px; margin-bottom: 25px; gap: 20px; flex-wrap: wrap; }}
                    .search-box {{ background: #020409; border: 2px solid #388bfd; color: #ffffff; padding: 12px 18px; border-radius: 8px; font-size: 15px; width: 350px; font-weight: 700; box-shadow: 0 0 10px rgba(56,139,253,0.1); }}
                    .search-box:focus {{ outline: none; border-color: #58a6ff; box-shadow: 0 0 15px rgba(88,166,255,0.3); }}
                    
                    .db-info {{ display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }}
                    .db-title {{ font-size: 13px; color: #8bc2ff; font-weight: 800; text-transform: uppercase; }}
                    .badge-container {{ display: flex; gap: 6px; flex-wrap: wrap; }}
                    .db-league-badge {{ background: #1f3a6d; color: #ffffff; font-weight: 900; font-size: 12px; padding: 5px 10px; border-radius: 6px; border: 1px solid #388bfd; }}

                    /* CALENDARIO MODIFICATO CON SCRITTE GIALLO OCRA */
                    .calendar-section {{ background: #091124; border: 2px solid #16264c; padding: 20px; border-radius: 12px; margin-bottom: 25px; }}
                    .calendar-title {{ font-size: 14px; font-weight: 800; text-transform: uppercase; color: #daa520; margin-bottom: 15px; letter-spacing: 0.5px; }}
                    .calendar-grid {{ display: flex; gap: 12px; flex-wrap: wrap; }}
                    
                    .cal-btn {{ flex: 1; min-width: 130px; padding: 14px 10px; border-radius: 8px; border: 2px solid #222; background: #111; color: #daa520 !important; text-align: center; cursor: pointer; font-weight: 800; transition: all 0.2s ease; }}
                    .cal-btn .cal-sub {{ font-size: 11px; font-weight: 700; color: #daa520 !important; opacity: 0.85; margin-top: 4px; display: block; }}
                    
                    /* Gli sfondi rimangono identici, ma applichiamo il colore giallo ocra forzato ai testi */
                    .cal-btn.cal-selected {{ background: #e0a904 !important; color: #daa520 !important; border-color: #ffea00 !important; box-shadow: 0 0 15px #e0a904; }}
                    .cal-btn.cal-hot {{ background: #4c1d95; border-color: #c084fc; }}
                    .cal-btn.cal-normal {{ background: #064e3b; border-color: #34d399; }}
                    .cal-btn.cal-empty {{ background: #2d0c0c; border-color: #7f1d1d; cursor: not-allowed; }}

                    .dashboard-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 25px; margin-bottom: 25px; }}
                    @media (max-width: 1300px) {{ .dashboard-grid {{ grid-template-columns: 1fr; }} }}
                    
                    .panel {{ background: #0a1122; border-radius: 12px; padding: 22px; transition: all 0.3s; }}
                    .panel-live {{ border: 2px solid #7a1c1c; box-shadow: 0 0 15px rgba(122,28,28,0.2); }}
                    .panel-future {{ border: 2px solid #b38600; box-shadow: 0 0 15px rgba(179,134,0,0.2); }}
                    .panel-leagues {{ border: 2px solid #1e366a; background: #060d1a; }}
                    
                    h2 {{ font-size: 18px; font-weight: 800; margin-top: 0; margin-bottom: 20px; padding-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid #222; }}
                    .live-title {{ color: #ff5252; text-shadow: 0 0 8px rgba(255,82,82,0.3); }}
                    .future-title {{ color: #ffc107; text-shadow: 0 0 8px rgba(255,193,7,0.3); }}
                    .leagues-title {{ color: #388bfd; text-shadow: 0 0 8px rgba(56,139,253,0.3); }}
                    
                    table {{ width: 100%; border-collapse: separate; border-spacing: 0; }}
                    th {{ background-color: #0f192f; color: #8bc2ff; text-align: left; padding: 14px 12px; font-size: 13px; font-weight: 800; text-transform: uppercase; border-bottom: 3px solid #1e366a; }}
                    td {{ padding: 16px 12px; border-bottom: 1px solid #162548; color: #ffffff; vertical-align: top; font-size: 14px; }}
                    tr.searchable-row:hover td {{ background-color: #121f3a; }}
                    
                    .time-badge {{ background: #451313; color: #ff5252; padding: 6px 10px; border-radius: 6px; font-weight: 800; border: 2px solid #ff5252; display: inline-block; font-size: 13px; }}
                    .time-badge.future {{ background: #3b2a07; color: #ffc107; border: 2px solid #ffc107; }}
                    
                    .match-team {{ font-weight: 800; font-size: 16px; color: #ffffff; margin-bottom: 6px; }}
                    .score-badge {{ font-size: 13px; color: #ff8787; background: #2d0e0e; padding: 4px 10px; border-radius: 5px; border: 1px solid #a82c2c; display: inline-block; margin-bottom: 6px; font-weight: 700; }}
                    .league-text {{ font-size: 12px; color: #8ba2c1; font-weight: 600; }}
                    
                    .analysis-cell {{ font-size: 14px; color: #ffffff; line-height: 1.6; white-space: pre-line; background: #070d1a; padding: 14px; border-radius: 8px; border-left: 5px solid #388bfd; border: 1px solid #16264c; }}
                    
                    .state-row-message {{ text-align: center; color: #8ba2c1; padding: 45px; font-style: italic; font-size: 15px; font-weight: 600; }}
                    b {{ color: #4da3ff; font-weight: 800; }} i {{ color: #cbd5e1; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>⚡ Millenium Trading Hub</h1>
                        <div class="status-bar">
                            <div class="badge badge-online">🟢 Radar Attivo</div>
                            <div class="badge badge-live-count">In Play: <span id="count-scanned">0</span></div>
                            <div class="badge">Alert Telegram: <span id="count-alerts">0</span></div>
                            <div class="badge">Aggiornato: <span id="time-updated">Mai</span></div>
                        </div>
                    </div>
                    
                    <div class="controls-panel">
                        <input type="text" id="searchBar" class="search-box" placeholder="🔍 Filtra squadre o campionati..." onkeyup="filterTables()">
                        <div class="db-info">
                            <span class="db-title">🗄️ Database Caricati:</span>
                            <div class="badge-container">{badge_campionati}</div>
                        </div>
                    </div>

                    <div class="calendar-section">
                        <div class="calendar-title">📅 CALENDARIO SETTIMANALE (Clicca un giorno per filtrare lo Studio Preventivo)</div>
                        <div class="calendar-grid" id="calendarContainer"></div>
                    </div>
                    
                    <div class="dashboard-grid">
                        <div class="panel panel-live">
                            <h2 class="live-title">🔴 Monitor Live Real-Time</h2>
                            <table>
                                <thead>
                                    <tr>
                                        <th style="width: 15%; text-align:center;">Minuto</th>
                                        <th style="width: 45%;">Incontro / Competizione</th>
                                        <th style="width: 15%; text-align:center;">Tiri Porta</th>
                                        <th style="width: 25%;">Suggerimento</th>
                                    </tr>
                                </thead>
                                <tbody id="live-tbody">
                                    <tr><td colspan='4' class="state-row-message">📡 Sincronizzazione flussi live in corso...</td></tr>
                                </tbody>
                            </table>
                        </div>
                        
                        <div class="panel panel-future">
                            <h2 class="future-title">⏳ Palinsesto Prossime Ore</h2>
                            <table>
                                <thead>
                                    <tr>
                                        <th style="width: 20%; text-align:center;">Inizio</th>
                                        <th style="width: 50%;">Match / Campionato</th>
                                        <th style="width: 30%;">Analisi Statistica</th>
                                    </tr>
                                </thead>
                                <tbody id="future-tbody">
                                    <tr><td colspan='3' class="state-row-message">📅 Sincronizzazione palinsesto in corso...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div class="panel panel-leagues">
                        <h2 class="leagues-title">📋 Campionati Monitorati dal Sistema (Legenda Database)</h2>
                        <table>
                            <thead>
                                <tr>
                                    <th style="width: 20%;">Sigla Archivio</th>
                                    <th style="width: 80%;">Nome Competizione 1xBet Originale</th>
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
                            
                            let classeColore = "cal-empty";
                            let subText = "(No Bet)";
                            
                            if (count > 0) {{
                                subText = count === 1 ? "[1 Match]" : `[${{count}} Match]`;
                                classeColore = count >= 5 ? "cal-hot" : "cal-normal";
                            }}
                            
                            if (g.id === giornoSelezionato) {{
                                classeColore = "cal-selected";
                            }}
                            
                            const btn = document.createElement('div');
                            btn.className = `cal-btn ${{classeColore}}`;
                            btn.innerHTML = `${{g.label}} <span class="cal-sub">${{subText}}</span>`;
                            
                            if (count > 0 || g.id === giorniSettimana[0].id) {{
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
                            futureTbody.innerHTML = `<tr><td colspan='3' class="state-row-message">📅 Nessun match in archivio programmato per la giornata selezionata.</td></tr>`;
                        }} else {{
                            let futureHtml = "";
                            matchFiltrati.forEach(mf => {{
                                futureHtml += `
                                    <tr class="searchable-row">
                                        <td style="text-align:center;"><span class="time-badge future">${{mf.data_ora}}</span></td>
                                        <td>
                                            <div class="match-team">${{mf.partita}}</div>
                                            <div class="league-text">🌍 ${{mf.campionato}}</div>
                                        </td>
                                        <td class="analysis-cell">${{mf.analisi}}</td>
                                    </tr>
                                `;
                            }});
                            futureTbody.innerHTML = futureHtml;
                        }}
                        filterTables();
                    }}

                    async function updateDashboard() {{
                        try {{
                            const response = await fetch('/api/data');
                            const data = await response.json();
                            
                            document.getElementById('count-scanned').innerText = data.partite_scansionate;
                            document.getElementById('count-alerts').innerText = data.alert_inviati_totale;
                            document.getElementById('time-updated').innerText = data.ultimo_aggiornamento;
                            
                            const liveTbody = document.getElementById('live-tbody');
                            if(!data.match_rilevanti || data.match_rilevanti.length === 0) {{
                                liveTbody.innerHTML = `<tr><td colspan='4' class="state-row-message">📡 In attesa di match live con tiri in porta attivi...</td></tr>`;
                            }} else {{
                                let liveHtml = "";
                                data.match_rilevanti.forEach(m => {{
                                    liveHtml += `
                                        <tr class="searchable-row">
                                            <td style="text-align:center;"><span class="time-badge">${{m.orario}}</span></td>
                                            <td>
                                                <div class="match-team">${{m.partita}}</div>
                                                <div class="score-badge">Risultato: ${{m.punteggio}}</div>
                                                <div class="league-text">🏆 ${{m.campionato}}</div>
                                            </td>
                                            <td style="text-align:center; color:#4af262; font-weight:bold; font-size:16px;">🔥 ${{m.tiri}}</td>
                                            <td class="analysis-cell">${{m.analisi}}</td>
                                        </tr>
                                    `;
                                }});
                                liveTbody.innerHTML = liveHtml;
                            }}
                            
                            cacheMatchFuturi = data.match_futuri || [];
                            renderCalendario(cacheMatchFuturi);
                            renderCalcoloPrematch();
                            
                        }} catch(err) {{
                            console.log(err);
                        }}
                    }}

                    function filterTables() {{
                        let query = document.getElementById('searchBar').value.toLowerCase();
                        let rows = document.querySelectorAll('.searchable-row');
                        rows.forEach(row => {{
                            if(row.innerText.toLowerCase().includes(query)) {{
                                row.style.display = "";
                            }} else {{
                                row.style.display = "none";
                            }}
                        }});
                    }}

                    setInterval(updateDashboard, 15000);
                    window.onload = updateDashboard;
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))
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
            
            output = f"🏠 Media Casa: {media_casa:.2f} | 🚀 Media Fuori: {media_fuori:.2f}\n"
            if is_live and minuto is not None:
                if somma_medie >= 2.40:
                    if minuto <= 35: output += "💰 <b>CONSIGLIO: OVER 0.5 HT (Quota > 1.70)</b>"
                    elif minuto <= 65: output += f"💰 <b>CONSIGLIO: OVER {gol_totali + 1.5} LIVE (Quota > 1.80)</b>"
                    elif minuto <= 82: output += f"💰 <b>CONSIGLIO: OVER {gol_totali + 0.5} FINALE</b>"
                    else: output += "⚠️ <i>No Bet (Fine match)</i>"
                else: output += "⚠️ <i>No Bet (Storico basso)</i>"
            else:
                if somma_medie >= 3.20: output += "💰 <b>STUDIO: Pendenza OVER 2.5</b>"
                elif somma_medie >= 2.40: output += "💰 <b>STUDIO: Ottimo OVER 1.5</b>"
                else: output += "⚠️ <i>STUDIO: Match da Under</i>"
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
                        "campionato": campeonato, "analisi": analizza_e_consiglia(nome_file_csv, squadra_casa, squadra_ospite, is_live=False)
                    })
            DASHBOARD_DATA["match_futuri"] = prossimi_match
            salva_dati_su_file()
    except Exception as e:
        print(f"⚠️ Timeout Prematch (Sbloccato): {e}", flush=True)

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
                    for stat in sc_data.get("S", []):
                        if stat.get("T") == 2:
                            tiri_porta_casa, tiri_porta_ospite = int(stat.get("G1", 0)), int(stat.get("G2", 0))
                            break
                    tiri_totali_live = tiri_porta_casa + tiri_porta_ospite
                    
                    if tiri_totali_live > 0:
                        nuovi_match_rilevanti.append({
                            "orario": f"{minuto_corrente}'", "partita": f"{squadra_casa} - {squadra_ospite}",
                            "punteggio": f"{gol_casa} - {gol_ospite}", "campionato": campionato_live,
                            "tiri": f"{tiri_totali_live}", "analisi": analizza_e_consiglia(nome_file_csv, squadra_casa, squadra_ospite, minuto=minuto_corrente, gol_totali=totale_gol_attuali, is_live=True)
                        })
                    if tiri_totali_live >= 5:
                        consiglio_text = analizza_e_consiglia(nome_file_csv, squadra_casa, squadra_ospite, minuto=minuto_corrente, gol_totali=totale_gol_attuali, is_live=True).replace("<b>", "*").replace("</b>", "*").replace("<i>", "_").replace("</i>", "_")
                        invia_telegram(f"⚽ *Match:* {squadra_casa} - {squadra_ospite}\n🎯 *Tiri:* {tiri_totali_live}\n📊 *Studio:*\n{consiglio_text}")
                        DASHBOARD_DATA["alert_inviati_totale"] += 1
                        time.sleep(2)
            DASHBOARD_DATA["match_rilevanti"] = nuovi_match_rilevanti
            salva_dati_su_file()
    except Exception as e:
        print(f"⚠️ Timeout Live (Sbloccato): {e}", flush=True)

def invia_telegram(messaggio):
    try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": messaggio, "parse_mode": "Markdown"}, timeout=5)
    except Exception: pass

if __name__ == "__main__":
    Thread(target=finto_server, daemon=True).start()
    print("Millenium Bot attivo!", flush=True)
    while True:
        scansione_partite_live()
        scansione_prematch()
        time.sleep(60)
