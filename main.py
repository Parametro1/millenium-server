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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

DASHBOARD_DATA = {
    "ultimo_aggiornamento": "Mai",
    "partite_scansionate": 0,
    "alert_inviati_totale": 0,
    "match_rilevanti": [],
    "match_futuri": []
}

DIZIONARIO_CAMPIONATI = {
    "Calcio. Inghilterra. Premier League": "E0",
    "Calcio. Inghilterra. Championship": "E1",
    "Calcio. Germania. Bundesliga": "D1",
    "Calcio. Germania. 2. Bundesliga": "D2",
    "Calcio. Italia. Serie A": "I1",
    "Calcio. Italia. Serie B": "I2",
    "Calcio. Olanda. Eredivisie": "N1",
    "Calcio. Spagna. Primera Division": "SP1",
    "Calcio. Spagna. Segunda Division": "SP2",
    "Calcio. Francia. Ligue 1": "F1",
    "Calcio. Francia. Ligue 2": "F2",
    "Calcio. Turchia. SuperLig": "T1",
    "Calcio. USA. MLS": "USA"
}

# Lista fissa ordinata di tutti i campionati per garantire che appaiano TUTTI
CAMPIONATI_ALL = ["E0", "D2", "E1", "I2", "SP1", "I1", "N1", "F2", "T1", "USA", "F1", "D1", "SP2"]

class DashboardHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args): 
        return

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
            
            # Generazione sicura di tutti i badge dei database storici
            badge_campionati = "".join([f"<span class='db-league-badge'>{sigla}</span>" for sigla in CAMPIONATI_ALL])

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Millenium — Trading Intelligence Hub</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif; background-color: #070a12; color: #cdddec; margin:0; padding:20px; }}
                    .container {{ max-width: 1650px; margin: 0 auto; }}
                    
                    /* Header Premium */
                    .header {{ background: linear-gradient(135deg, #0f1626 0%, #141f36 100%); padding: 20px 30px; border-radius: 16px; border: 1px solid #1e2d4a; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; box-shadow: 0 8px 32px rgba(0,0,0,0.4); }}
                    h1 {{ color: #ffffff; margin: 0; font-size: 22px; font-weight: 700; display: flex; align-items: center; gap: 12px; }}
                    .status-bar {{ display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }}
                    
                    .badge {{ background: #0b1120; color: #9ab0c7; padding: 8px 14px; border-radius: 8px; border: 1px solid #17243c; font-size: 13px; font-weight: 600; }}
                    .badge span {{ color: #388bfd; font-weight: bold; font-family: monospace; font-size: 14px; }}
                    .badge-online {{ background: rgba(56, 139, 253, 0.12); color: #58a6ff; border-color: rgba(56, 139, 253, 0.4); padding-left: 25px; position: relative; }}
                    .badge-online::before {{ content: ''; position: absolute; left: 11px; top: 14px; width: 8px; height: 8px; background-color: #388bfd; border-radius: 50%; box-shadow: 0 0 10px #388bfd; animation: blink 1.5s infinite; }}

                    /* Pannello Controlli Corretto per allineamento */
                    .controls-panel {{ display: flex; justify-content: space-between; align-items: center; background: #0f1626; border: 1px solid #1b283f; padding: 15px 25px; border-radius: 12px; margin-bottom: 25px; gap: 20px; flex-wrap: wrap; }}
                    .search-box {{ background: #070a12; border: 1px solid #223754; color: #ffffff; padding: 10px 18px; border-radius: 8px; font-size: 13px; width: 320px; transition: all 0.3s; }}
                    .search-box:focus {{ outline: none; border-color: #388bfd; box-shadow: 0 0 8px rgba(56,139,253,0.3); }}
                    
                    .db-info {{ display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }}
                    .db-title {{ font-size: 13px; color: #90a4ae; font-weight: 600; white-space: nowrap; }}
                    .badge-container {{ display: flex; gap: 6px; flex-wrap: wrap; }}
                    .db-league-badge {{ background: #16243a; color: #58a6ff; font-weight: bold; font-size: 11px; padding: 4px 9px; border-radius: 4px; border: 1px solid #223a5e; display: inline-block; }}

                    /* Layout */
                    .dashboard-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 25px; }}
                    @media (max-width: 1200px) {{ .dashboard-grid {{ grid-template-columns: 1fr; }} }}
                    
                    .panel {{ background: #0f1626; border-radius: 16px; border: 1px solid #1b283f; padding: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }}
                    h2 {{ font-size: 16px; font-weight: 600; margin-top: 0; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #1a2942; display: flex; align-items: center; gap: 10px; }}
                    .live-title {{ color: #ff5252; }}
                    .future-title {{ color: #ffab40; }}
                    
                    table {{ width: 100%; border-collapse: separate; border-spacing: 0; }}
                    th {{ background-color: #162238; color: #90a4ae; text-align: left; padding: 12px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 2px solid #223554; }}
                    th:first-child {{ border-top-left-radius: 8px; border-bottom-left-radius: 8px; }}
                    th:last-child {{ border-top-right-radius: 8px; border-bottom-right-radius: 8px; }}
                    td {{ padding: 14px 12px; border-bottom: 1px solid #162238; color: #cfd8dc; vertical-align: top; }}
                    tr:last-child td {{ border-bottom: none; }}
                    tr.searchable-row:hover td {{ background-color: #131e33; }}
                    
                    .time-badge {{ background: rgba(239, 68, 68, 0.12); color: #ff5252; padding: 4px 8px; border-radius: 6px; font-weight: 700; font-size: 12px; border: 1px solid rgba(239, 68, 68, 0.25); display: inline-block; font-family: monospace; }}
                    .time-badge.future {{ background: rgba(245, 158, 11, 0.12); color: #ffab40; border: 1px solid rgba(245, 158, 11, 0.25); }}
                    .match-team {{ font-weight: 700; font-size: 14px; color: #ffffff; margin-bottom: 5px; }}
                    .score-badge {{ font-size: 11px; color: #ffa198; background: rgba(239, 68, 68, 0.05); padding: 2px 6px; border-radius: 4px; display: inline-block; margin-bottom: 5px; border: 1px solid rgba(239, 68, 68, 0.15); }}
                    .league-text {{ font-size: 11px; color: #90a4ae; }}
                    
                    .analysis-cell {{ font-size: 12px; color: #eceff1; line-height: 1.5; white-space: pre-line; background: rgba(255,255,255,0.01); padding: 10px; border-radius: 6px; border-left: 3px solid #388bfd; }}
                    
                    b {{ color: #64b5f6; font-weight: 700; background: rgba(100, 181, 246, 0.08); padding: 1px 4px; border-radius: 4px; }}
                    i {{ color: #90a4ae; font-style: italic; }}
                    
                    @keyframes blink {{ 0% {{ opacity: 0.4; }} 50% {{ opacity: 1; }} 100% {{ opacity: 0.4; }} }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>⚡ Millenium Intelligence Dashboard</h1>
                        <div class="status-bar">
                            <div class="badge badge-online">Radar Attivo</div>
                            <div class="badge">In Play: <span id="count-scanned">0</span></div>
                            <div class="badge">Alert Telegram: <span id="count-alerts">0</span></div>
                            <div class="badge">Aggiornato: <span id="time-updated">Mai</span></div>
                        </div>
                    </div>
                    
                    <!-- Box controlli sistemato -->
                    <div class="controls-panel">
                        <input type="text" id="searchBar" class="search-box" placeholder="🔍 Filtra squadre o campionati..." onkeyup="filterTables()">
                        <div class="db-info">
                            <span class="db-title">🗄️ Database Storici Caricati:</span>
                            <div class="badge-container">{badge_campionati}</div>
                        </div>
                    </div>
                    
                    <div class="dashboard-grid">
                        <!-- LIVE PANEL -->
                        <div class="panel">
                            <h2 class="live-title">🔴 Monitor Live Real-Time (Filtro Tiri attivi)</h2>
                            <table>
                                <thead>
                                    <tr>
                                        <th style="width: 15%; text-align:center;">Minuto</th>
                                        <th style="width: 45%;">Incontro / Competizione</th>
                                        <th style="width: 15%; text-align:center;">Tiri Porta</th>
                                        <th style="width: 25%;">Suggerimento Algoritmo</th>
                                    </tr>
                                </thead>
                                <tbody id="live-tbody">
                                    <tr id="live-empty-row"><td colspan='4' style='text-align:center; color:#90a4ae; padding:40px; font-style:italic;'>📡 In attesa di match live che soddisfino i criteri dei tiri in porta...</td></tr>
                                </tbody>
                            </table>
                        </div>
                        
                        <!-- PREMATCH PANEL -->
                        <div class="panel">
                            <h2 class="future-title">⏳ Palinsesto Prossime Ore (Studio Preventivo)</h2>
                            <table>
                                <thead>
                                    <tr>
                                        <th style="width: 20%; text-align:center;">Inizio</th>
                                        <th style="width: 50%;">Match / Campionato</th>
                                        <th style="width: 30%;">Analisi Statistica Archivio</th>
                                    </tr>
                                </thead>
                                <tbody id="future-tbody">
                                    <tr id="future-empty-row"><td colspan='3' style='text-align:center; color:#90a4ae; padding:40px; font-style:italic;'>📅 Nessun match in archivio programmato per le prossime ore.</td></tr>
                                </tbody>
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
                            
                            // Gestione Tabella Live
                            const liveTbody = document.getElementById('live-tbody');
                            if(data.match_rilevanti.length === 0) {{
                                liveTbody.innerHTML = `<tr id="live-empty-row"><td colspan='4' style='text-align:center; color:#90a4ae; padding:40px; font-style:italic;'>📡 In attesa di match live che soddisfino i criteri dei tiri in porta...</td></tr>`;
                            }} else {{
                                let liveHtml = "";
                                data.match_rilevanti.forEach(m => {{
                                    let tiriNum = parseInt(m.tiri) || 0;
                                    let icon = tiriNum >= 6 ? "🔥 " : "📊 ";
                                    liveHtml += `
                                        <tr class="searchable-row">
                                            <td style="text-align:center;"><span class="time-badge">${{m.orario}}</span></td>
                                            <td>
                                                <div class="match-team">${{m.partita}}</div>
                                                <div class="score-badge">Risultato: ${{m.punteggio}}</div>
                                                <div class="league-text">🏆 ${{m.campionato}}</div>
                                            </td>
                                            <td style="text-align:center; color:#3fb950; font-weight:bold; font-size:15px;">
                                                <span>${{icon}}</span>${{m.tiri}}
                                            </td>
                                            <td class="analysis-cell">${{m.analisi}}</td>
                                        </tr>
                                    `;
                                }});
                                liveTbody.innerHTML = liveHtml;
                            }}
                            
                            // Gestione Tabella Futuri
                            const futureTbody = document.getElementById('future-tbody');
                            if(data.match_futuri.length === 0) {{
                                futureTbody.innerHTML = `<tr id="future-empty-row"><td colspan='3' style='text-align:center; color:#90a4ae; padding:40px; font-style:italic;'>📅 Nessun match in archivio programmato per le prossime ore.</td></tr>`;
                            }} else {{
                                let futureHtml = "";
                                data.match_futuri.forEach(mf => {{
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
                            
                            // Mantieni attivo il filtro se l'utente sta scrivendo durante il refresh automatico
                            filterTables();
                            
                        }} catch(err) {{
                            console.log("Errore sincronizzazione asincrona:", err);
                        }}
                    }}

                    // Funzione di Filtro Intelligente corretta (ignora le scritte di stato vuoto)
                    function filterTables() {{
                        let query = document.getElementById('searchBar').value.toLowerCase();
                        let rows = document.querySelectorAll('.searchable-row');
                        
                        rows.forEach(row => {{
                            let text = row.innerText.toLowerCase();
                            if(text.includes(query)) {{
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
    except Exception:
        pass

# =======================================================
# LOGICHE DI ANALISI STORICA E LIVE VALUTATA
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
            
            media_casa = 0.0
            media_fuori = 0.0
            output = ""
            
            if not partite_casa.empty and 'FTHG' in df.columns:
                media_casa = partite_casa['FTHG'].mean()
                output += f"🏠 Media Gol Casa: {media_casa:.2f}\n"
            if not partite_ospite.empty and 'FTAG' in df.columns:
                media_fuori = partite_ospite['FTAG'].mean()
                output += f"🚀 Media Gol Fuori: {media_fuori:.2f}\n"
            
            somma_medie = media_casa + media_fuori
            
            if is_live and minuto is not None:
                output += f"📋 Analisi al minuto {minuto}':\n"
                if somma_medie >= 2.40:
                    if minuto <= 35:
                        output += "💰 <b>CONSIGLIO: OVER 0.5 HT (Quota > 1.70)</b>"
                    elif minuto > 35 and minuto <= 65:
                        output += f"💰 <b>CONSIGLIO: OVER {gol_totali + 1.5} LIVE (Quota > 1.80)</b>"
                    elif minuto > 65 and minuto <= 82:
                        output += f"💰 <b>CONSIGLIO: OVER {gol_totali + 0.5} FINALE (Pressione)</b>"
                    else:
                        output += "⚠️ <i>CONSIGLIO: No Bet (Fine match)</i>"
                else:
                    output += "⚠️ <i>CONSIGLIO: No Bet (Storico basso)</i>"
            else:
                if somma_medie >= 3.20:
                    output += "💰 <b>STUDIO: Pendenza OVER 2.5</b>"
                elif somma_medie >= 2.40:
                    output += "💰 <b>STUDIO: Ottimo OVER 1.5</b>"
                elif somma_medie > 0:
                    output += "⚠️ <i>STUDIO: Match da Under</i>"
                else:
                    output = "Dati storici insufficienti."
                
            return output
        return "File archivio non trovato."
    except Exception:
        return "Errore calcolo medie."

def scansione_prematch():
    try:
        response = requests.get(URL_FUTURE, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            dati = response.json()
            partite = dati.get("Value", [])
            prossimi_match = []
            
            for partita in partite:
                campionato = partita.get("L", "")
                squadra_casa = partita.get("O1", "")
                squadra_ospite = partita.get("O2", "")
                timestamp_inizio = partita.get("S", 0)
                
                if campeonato in DIZIONARIO_CAMPIONATI and timestamp_inizio > 0:
                    nome_file_csv = DIZIONARIO_CAMPIONATI[campionato]
                    ora_inizio = time.strftime('%d/%m %H:%M', time.localtime(timestamp_inizio))
                    consiglio_match = analizza_e_consiglia(nome_file_csv, squadra_casa, squadra_ospite, is_live=False)
                    
                    prossimi_match.append({
                        "data_ora": ora_inizio,
                        "partita": f"{squadra_casa} - {squadra_ospite}",
                        "campionato": campionato,
                        "analisi": consiglio_match
                    })
            DASHBOARD_DATA["match_futuri"] = prossimi_match[:15]
    except Exception as e:
        print(f"Errore scansione prematch: {e}", flush=True)

def scansione_partite_live():
    try:
        response = requests.get(URL_LIVE, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            dati = response.json()
            partite = dati.get("Value", [])
            DASHBOARD_DATA["partite_scansionate"] = len(partite)
            DASHBOARD_DATA["ultimo_aggiornamento"] = time.strftime("%H:%M:%S")
            nuovi_match_rilevanti = []
            
            for partita in partite:
                campionato_live = partita.get("L", "")
                squadra_casa = partita.get("O1", "")
                squadra_ospite = partita.get("O2", "")
                
                if campionato_live in DIZIONARIO_CAMPIONATI:
                    nome_file_csv = DIZIONARIO_CAMPIONATI[campionato_live]
                    
                    sc_data = partita.get("SC", {})
                    tempo_secondi = sc_data.get("TS", 0)
                    minuto_corrente = int(tempo_secondi // 60) if tempo_secondi > 0 else 1
                    
                    gol_casa = int(sc_data.get("FS", {}).get("G1", 0))
                    gol_ospite = int(sc_data.get("FS", {}).get("G2", 0))
                    totale_gol_attuali = gol_casa + gol_ospite
                    stringa_punteggio = f"{gol_casa} - {gol_ospite}"
                    
                    stats = sc_data.get("S", [])
                    tiri_porta_casa = 0
                    tiri_porta_ospite = 0
                    for stat in stats:
                        if stat.get("T") == 2:
                            tiri_porta_casa = int(stat.get("G1", 0))
                            tiri_porta_ospite = int(stat.get("G2", 0))
                            break
                    tiri_totali_live = tiri_porta_casa + tiri_porta_ospite
                    
                    if tiri_totali_live > 0:
                        consiglio_live = analizza_e_consiglia(
                            nome_file_csv, squadra_casa, squadra_ospite, 
                            minuto=minuto_corrente, gol_totali=totale_gol_attuali, is_live=True
                        )
                        nuovi_match_rilevanti.append({
                            "orario": f"{minuto_corrente}'",
                            "partita": f"{squadra_casa} - {squadra_ospite}",
                            "punteggio": stringa_punteggio,
                            "campionato": campionato_live,
                            "tiri": f"{tiri_totali_live}",
                            "analisi": consiglio_live
                        })
                    
                    if tiri_totali_live >= 5:
                        consiglio_telegram = analizza_e_consiglia(
                            nome_file_csv, squadra_casa, squadra_ospite, 
                            minuto=minuto_corrente, gol_totali=totale_gol_attuali, is_live=True
                        )
                        consiglio_text = consiglio_telegram.replace("<b>", "*").replace("</b>", "*").replace("<i>", "_").replace("</i>", "_")
                        
                        messaggio = (
                            f"*MILLENIUM BOT - COPERTURA LIVE VALUTATA*\n\n"
                            f"⚽ *Match:* {squadra_casa} - {squadra_ospite} ({stringa_punteggio})\n"
                            f"🏆 *Torneo:* {campionato_live}\n"
                            f"⏱️ *Minuto:* {minuto_corrente}' minuto\n\n"
                            f"🎯 *STATISTICHE LIVE:* Tiri totali {tiri_totali_live} ({tiri_porta_casa}-{tiri_porta_ospite})\n\n"
                            f"📊 *STUDIO DINAMICO PROGETTATO:*\n{consiglio_text}\n\n"
                            f"🍀 _Attendi che la quota di mercato tocchi il valore consigliato sul tuo bookmaker prima di piazzare!_"
                        )
                        invia_telegram(messaggio)
                        DASHBOARD_DATA["alert_inviati_totale"] += 1
                        time.sleep(5)
            DASHBOARD_DATA["match_rilevanti"] = nuovi_match_rilevanti
    except Exception as e:
        print(f"Errore live: {e}", flush=True)

def invia_telegram(messaggio):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": messaggio, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception:
        pass

if __name__ == "__main__":
    Thread(target=finto_server, daemon=True).start()
    print("Millenium Bot attivo!", flush=True)
    
    while True:
        scansione_partite_live()
        scansione_prematch()
        time.sleep(60)
