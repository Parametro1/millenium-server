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

# Forza la chiusura delle connessioni appese a livello di network
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

CAMPIONATI_ALL = ["E0", "D2", "E1", "I2", "SP1", "I1", "N1", "F2", "T1", "USA", "F1", "D1", "SP2"]

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
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Millenium — Trading Intelligence Hub</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background-color: #080c14; color: #ffffff; margin:0; padding:20px; }}
                    .container {{ max-width: 1600px; margin: 0 auto; }}
                    .header {{ background: #111c36; padding: 22px 30px; border-radius: 12px; border: 2px solid #253b6e; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; }}
                    h1 {{ color: #ffffff; margin: 0; font-size: 25px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; }}
                    .status-bar {{ display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }}
                    .badge {{ background: #050912; color: #ffffff; padding: 10px 16px; border-radius: 8px; border: 2px solid #253b6e; font-size: 14px; font-weight: 700; }}
                    .badge span {{ color: #388bfd; font-weight: 900; font-family: monospace; font-size: 15px; }}
                    .badge-online {{ background: #1f4225; color: #4af262; border-color: #2ea44f; }}
                    .controls-panel {{ display: flex; justify-content: space-between; align-items: center; background: #111c36; border: 2px solid #253b6e; padding: 20px; border-radius: 12px; margin-bottom: 25px; gap: 20px; flex-wrap: wrap; }}
                    .search-box {{ background: #03060d; border: 2px solid #388bfd; color: #ffffff; padding: 12px 18px; border-radius: 8px; font-size: 15px; width: 350px; font-weight: 700; }}
                    .db-info {{ display: flex; align-items: center; gap: 15px; flex-wrap: wrap; }}
                    .db-title {{ font-size: 14px; color: #ffffff; font-weight: 800; text-transform: uppercase; }}
                    .badge-container {{ display: flex; gap: 6px; flex-wrap: wrap; }}
                    .db-league-badge {{ background: #388bfd; color: #ffffff; font-weight: 900; font-size: 13px; padding: 6px 12px; border-radius: 6px; border: 1px solid #ffffff; }}
                    .dashboard-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 25px; }}
                    @media (max-width: 1200px) {{ .dashboard-grid {{ grid-template-columns: 1fr; }} }}
                    .panel {{ background: #0d1527; border-radius: 12px; border: 2px solid #1e2d4a; padding: 22px; }}
                    h2 {{ font-size: 19px; font-weight: 800; margin-top: 0; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 2px solid #1e2d4a; text-transform: uppercase; }}
                    .live-title {{ color: #ff6b6b; }} .future-title {{ color: #ffd166; }}
                    table {{ width: 100%; border-collapse: separate; border-spacing: 0; }}
                    th {{ background-color: #16223f; color: #ffffff; text-align: left; padding: 14px 12px; font-size: 13px; font-weight: 800; border-bottom: 3px solid #253b6e; }}
                    td {{ padding: 16px 12px; border-bottom: 1px solid #1e2d4a; color: #ffffff; vertical-align: top; font-size: 14px; }}
                    .time-badge {{ background: #451a1a; color: #ff6b6b; padding: 6px 10px; border-radius: 6px; font-weight: 800; border: 2px solid #ff6b6b; display: inline-block; }}
                    .time-badge.future {{ background: #3b2f11; color: #ffd166; border: 2px solid #ffd166; }}
                    .match-team {{ font-weight: 800; font-size: 16px; margin-bottom: 6px; }}
                    .score-badge {{ font-size: 13px; color: #ff8787; background: #3b1717; padding: 4px 10px; border-radius: 5px; border: 1px solid #ff6b6b; display: inline-block; }}
                    .league-text {{ font-size: 13px; color: #a2b4ce; }}
                    .analysis-cell {{ font-size: 14px; white-space: pre-line; background: #111c36; padding: 14px; border-radius: 8px; border-left: 5px solid #388bfd; border: 1px solid #253b6e; }}
                    .state-row-message {{ text-align: center; color: #a2b4ce; padding: 45px; font-style: italic; }}
                    b {{ color: #4da3ff; font-weight: 800; }} i {{ color: #cbd5e1; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>⚡ Millenium Trading Hub</h1>
                        <div class="status-bar">
                            <div class="badge badge-online">🟢 Radar Attivo</div>
                            <div class="badge">In Play: <span id="count-scanned">0</span></div>
                            <div class="badge">Alert Telegram: <span id="count-alerts">0</span></div>
                            <div class="badge">Aggiornato: <span id="time-updated">Mai</span></div>
                        </div>
                    </div>
                    <div class="controls-panel">
                        <input type="text" id="searchBar" class="search-box" placeholder="🔍 Scansiona squadre..." onkeyup="filterTables()">
                        <div class="db-info"><span class="db-title">🗄️ Database:</span><div class="badge-container">{badge_campionati}</div></div>
                    </div>
                    <div class="dashboard-grid">
                        <div class="panel">
                            <h2 class="live-title">🔴 Monitor Live Real-Time</h2>
                            <table>
                                <thead><tr><th>Minuto</th><th>Incontro</th><th>Tiri Porta</th><th>Suggerimento</th></tr></thead>
                                <tbody id="live-tbody"><tr><td colspan='4' class="state-row-message">📡 Sincronizzazione flussi live in corso...</td></tr></tbody>
                            </table>
                        </div>
                        <div class="panel">
                            <h2 class="future-title">⏳ Palinsesto Prossime Ore</h2>
                            <table>
                                <thead><tr><th>Inizio</th><th>Match</th><th>Analisi Statistica</th></tr></thead>
                                <tbody id="future-tbody"><tr><td colspan='3' class="state-row-message">📅 Sincronizzazione palinsesto in corso...</td></tr></tbody>
                            </table>
                        </div>
                    </div>
                </div>
                <script>
                    async function updateDashboard() {{
                        try {{
                            const response = await fetch('/api/data');
                            const data = await response.json();
                            document.getElementById('count-scanned').innerText = data.partite_scansionate;
                            document.getElementById('count-alerts').innerText = data.alert_inviati_totale;
                            document.getElementById('time-updated').innerText = data.ultimo_aggiornamento;
                            
                            const liveTbody = document.getElementById('live-tbody');
                            if(!data.match_rilevanti || data.match_rilevanti.length === 0) {{
                                liveTbody.innerHTML = `<tr><td colspan='4' class="state-row-message">📡 In attesa di match live con tiri in porta...</td></tr>`;
                            }} else {{
                                let liveHtml = "";
                                data.match_rilevanti.forEach(m => {{
                                    liveHtml += `<tr><td><span class="time-badge">${{m.orario}}</span></td><td><div class="match-team">${{m.partita}}</div><div class="score-badge">${{m.punteggio}}</div><div class="league-text">🏆 ${{m.campionato}}</div></td><td style="color:#4af262; font-weight:bold; font-size:16px;">🔥 ${{m.tiri}}</td><td class="analysis-cell">${{m.analisi}}</td></tr>`;
                                }});
                                liveTbody.innerHTML = liveHtml;
                            }}
                            const futureTbody = document.getElementById('future-tbody');
                            if(!data.match_futuri || data.match_futuri.length === 0) {{
                                futureTbody.innerHTML = `<tr><td colspan='3' class="state-row-message">📅 Nessun match in archivio nelle prossime ore.</td></tr>`;
                            }} else {{
                                let futureHtml = "";
                                data.match_futuri.forEach(mf => {{
                                    futureHtml += `<tr><td><span class="time-badge future">${{mf.data_ora}}</span></td><td><div class="match-team">${{mf.partita}}</div><div class="league-text">🌍 ${{mf.campionato}}</div></td><td class="analysis-cell">${{mf.analisi}}</td></tr>`;
                                }});
                                futureTbody.innerHTML = futureHtml;
                            }}
                        }} catch(err) {{ console.log(err); }}
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
                    if minuto <= 35: output += "💰 <b>OVER 0.5 HT (Quota > 1.70)</b>"
                    elif minuto <= 65: output += f"💰 <b>OVER {gol_totali + 1.5} LIVE (Quota > 1.80)</b>"
                    elif minuto <= 82: output += f"💰 <b>OVER {gol_totali + 0.5} FINALE</b>"
                    else: output += "⚠️ <i>No Bet (Fine match)</i>"
                else: output += "⚠️ <i>No Bet (Storico basso)</i>"
            else:
                if somma_medie >= 3.20: output += "💰 <b>Pendenza OVER 2.5</b>"
                elif somma_medie >= 2.40: output += "💰 <b>Ottimo OVER 1.5</b>"
                else: output += "⚠️ <i>Match da Under</i>"
            return output
        return "File archivio non trovato."
    except Exception: return "Errore calcolo medie."

def scansione_prematch():
    try:
        # Timeout corto a 15 secondi per evitare congelamenti delle librerie di rete
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
            DASHBOARD_DATA["match_futuri"] = prossimi_match[:15]
            salva_dati_su_file()
    except Exception as e:
        print(f"⚠️ Timeout Prematch (Saltato per sicurezza): {e}", flush=True)

def scansione_partite_live():
    try:
        # Timeout corto a 15 secondi per evitare congelamenti delle librerie di rete
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
        print(f"⚠️ Timeout Live (Saltato per sicurezza): {e}", flush=True)

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
