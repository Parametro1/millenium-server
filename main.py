from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import os
import time
import requests
import pandas as pd
from threading import Thread

# ==========================================
# CONFIGURAZIONI PRINCIPALES
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
    "match_rilevanti": [],
    "match_futuri": []
}

DIZIONARIO_CAMPIONATI = {
    "Calcio. Italia. Serie A": "I1",
    "Calcio. Italia. Serie B": "I2",
    "Calcio. Inghilterra. Premier League": "E0",
    "Calcio. Inghilterra. Championship": "E1",
    "Calcio. Spagna. Primera Division": "SP1",
    "Calcio. Spagna. Segunda Division": "SP2",
    "Calcio. Germania. Bundesliga": "D1",
    "Calcio. Germania. 2. Bundesliga": "D2",
    "Calcio. Francia. Ligue 1": "F1",
    "Calcio. Francia. Ligue 2": "F2",
    "Calcio. Olanda. Eredivisie": "N1",
    "Calcio. Turchia. SuperLig": "T1",
    "Calcio. USA. MLS": "USA"
}

# =======================================================
# DASHBOARD WEB FUTURISTICA E COMPLETA
# =======================================================
class DashboardHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args): 
        return

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            
            # 1. Costruzione tabella LIVE
            righe_live = ""
            if not DASHBOARD_DATA["match_rilevanti"]:
                righe_live = "<tr><td colspan='4' style='text-align:center; color:#8b949e; padding:45px; font-style: italic;'>📡 In attesa di match live che soddisfino i criteri dei tiri in porta...</td></tr>"
            else:
                for m in DASHBOARD_DATA["match_rilevanti"]:
                    tiri_num = int(m['tiri']) if m['tiri'].isdigit() else 0
                    icona_tendenza = "🔥" if tiri_num >= 6 else "📊"
                    righe_live += f"""
                    <tr>
                        <td style='text-align:center;'><span class='time-badge'>{m['orario']}</span></td>
                        <td>
                            <div class='match-team'>{m['partita']}</div>
                            <div class='score-badge'>Risultato: {m['punteggio']}</div>
                            <div class='league-text'>🏆 {m['campionato']}</div>
                        </td>
                        <td style='text-align:center; color:#3fb950; font-weight:bold; font-size:16px;'>
                            <span style='font-size:12px; margin-right:3px;'>{icona_tendenza}</span>{m['tiri']}
                        </td>
                        <td class='analysis-cell'>{m['analisi']}</td>
                    </tr>
                    """

            # 2. Costruzione tabella MATCH FUTURI
            righe_future = ""
            if not DASHBOARD_DATA["match_futuri"]:
                righe_future = "<tr><td colspan='3' style='text-align:center; color:#8b949e; padding:45px; font-style: italic;'>📅 Nessun match in archivio programmato per le prossime ore.</td></tr>"
            else:
                for mf in DASHBOARD_DATA["match_futuri"]:
                    righe_future += f"""
                    <tr>
                        <td style='text-align:center;'><span class='time-badge future'>{mf['data_ora']}</span></td>
                        <td>
                            <div class='match-team'>{mf['partita']}</div>
                            <div class='league-text'>🌍 {mf['campionato']}</div>
                        </td>
                        <td class='analysis-cell'>{mf['analisi']}</td>
                    </tr>
                    """

            # 3. Lista dinamica dei campionati attivi nel sistema
            badge_campionati = "".join([f"<span class='db-league-badge'>{sigla}</span>" for sigla in set(DIZIONARIO_CAMPIONATI.values())])

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Millenium Bot — Advanced Intelligence Hub</title>
                <meta http-equiv="refresh" content="30">
                <style>
                    body {{ font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif; background-color: #090d16; color: #cddecb; margin:0; padding:30px; }}
                    .container {{ max-width: 1650px; margin: 0 auto; }}
                    
                    /* Header con Effetto Glow Neon */
                    .header {{ background: linear-gradient(135deg, #121824 0%, #161f30 100%); padding: 25px 35px; border-radius: 16px; border: 1px solid #24344d; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 8px 32px rgba(0,0,0,0.5); }}
                    h1 {{ color: #ffffff; margin: 0; font-size: 24px; font-weight: 700; letter-spacing: -0.5px; display: flex; align-items: center; gap: 12px; }}
                    .status-bar {{ display: flex; gap: 15px; align-items: center; }}
                    
                    /* Badge di Monitoraggio Avanzati */
                    .badge {{ background: #111a2e; color: #bcccda; padding: 8px 14px; border-radius: 8px; border: 1px solid #1f2f4d; font-size: 13px; font-weight: 600; box-shadow: inset 0 2px 4px rgba(0,0,0,0.2); }}
                    .badge span {{ color: #388bfd; font-weight: bold; font-family: monospace; font-size: 14px; }}
                    .badge-online {{ background: rgba(56, 139, 253, 0.12); color: #58a6ff; border-color: rgba(56, 139, 253, 0.4); text-transform: uppercase; letter-spacing: 0.5px; position: relative; padding-left: 25px; }}
                    .badge-online::before {{ content: ''; position: absolute; left: 10px; top: 13px; width: 8px; height: 8px; background-color: #58a6ff; border-radius: 50%; box-shadow: 0 0 10px #58a6ff; animation: blink 1.5s infinite; }}

                    /* Pannello Info Archivio */
                    .info-panel {{ background: #0e1726; border: 1px dashed #223754; padding: 12px 20px; border-radius: 10px; margin-bottom: 25px; display: flex; align-items: center; gap: 15px; font-size: 13px; color: #8ba2bd; }}
                    .db-league-badge {{ background: #1c2b42; color: #58a6ff; font-weight: bold; font-size: 11px; padding: 3px 8px; border-radius: 4px; margin-right: 5px; border: 1px solid #283e5e; }}

                    /* Layout Due Colonne */
                    .dashboard-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }}
                    @media (max-width: 1200px) {{ .dashboard-grid {{ grid-template-columns: 1fr; }} }}
                    
                    /* Stile dei Pannelli delle Tabelle */
                    .panel {{ background: #111827; border-radius: 16px; border: 1px solid #212b36; padding: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); transition: border-color 0.3s; }}
                    .panel:hover {{ border-color: #2b3a4a; }}
                    h2 {{ font-size: 18px; font-weight: 600; margin-top: 0; margin-bottom: 22px; padding-bottom: 12px; border-bottom: 1px solid #1f2937; display: flex; align-items: center; gap: 10px; }}
                    .live-title {{ color: #ff5252; }}
                    .future-title {{ color: #ffab40; }}
                    
                    /* Tabelle Strutturate */
                    table {{ width: 100%; border-collapse: separate; border-spacing: 0; }}
                    th {{ background-color: #1f2937; color: #9ca3af; text-align: left; padding: 14px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 2px solid #374151; }}
                    th:first-child {{ border-top-left-radius: 8px; border-bottom-left-radius: 8px; }}
                    th:last-child {{ border-top-right-radius: 8px; border-bottom-right-radius: 8px; }}
                    td {{ padding: 16px 14px; border-bottom: 1px solid #1f2937; color: #e5e7eb; vertical-align: top; }}
                    tr:last-child td {{ border-bottom: none; }}
                    tr:hover td {{ background-color: #172030; }}
                    
                    /* Badge di Contorno */
                    .time-badge {{ background: rgba(239, 68, 68, 0.15); color: #ef4444; padding: 5px 10px; border-radius: 6px; font-weight: 700; font-size: 12px; border: 1px solid rgba(239, 68, 68, 0.3); display: inline-block; font-family: monospace; }}
                    .time-badge.future {{ background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }}
                    .match-team {{ font-weight: 700; font-size: 15px; color: #ffffff; margin-bottom: 6px; letter-spacing: -0.2px; }}
                    .score-badge {{ font-size: 12px; color: #f87171; background: rgba(239, 68, 68, 0.08); padding: 3px 8px; border-radius: 5px; display: inline-block; margin-bottom: 6px; border: 1px solid rgba(239, 68, 68, 0.15); font-weight: 600; }}
                    .league-text {{ font-size: 12px; color: #9ca3af; font-weight: 500; }}
                    .analysis-cell {{ font-size: 13px; color: #d1d5db; line-height: 1.6; white-space: pre-line; background: rgba(255,255,255,0.01); padding: 10px; border-radius: 6px; border-left: 3px solid #3b82f6; }}
                    
                    /* Evidenziazione Stili all'interno delle analisi */
                    b {{ color: #60a5fa; font-weight: 700; background: rgba(96, 165, 250, 0.08); padding: 2px 4px; border-radius: 4px; }}
                    i {{ color: #9ca3af; font-style: italic; }}
                    
                    @keyframes blink {{
                        0% {{ opacity: 0.4; }}
                        50% {{ opacity: 1; }}
                        100% {{ opacity: 0.4; }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <!-- Intestazione -->
                    <div class="header">
                        <h1>⚡ Millenium Intelligence Dashboard</h1>
                        <div class="status-bar">
                            <div class="badge badge-online">Radar Live Attivo</div>
                            <div class="badge">In Play: <span>{DASHBOARD_DATA["partite_scansionate"]}</span></div>
                            <div class="badge">Aggiornato: <span>{DASHBOARD_DATA["ultimo_aggiornamento"]}</span></div>
                        </div>
                    </div>
                    
                    <!-- Barra info database -->
                    <div class="info-panel">
                        <strong>🗄️ Database Storici Caricati nel Sistema:</strong>
                        <div>{badge_campionati}</div>
                    </div>
                    
                    <!-- Griglia Layout -->
                    <div class="dashboard-grid">
                        
                        <!-- SEZIONE LIVE -->
                        <div class="panel">
                            <h2 class="live-title">🔴 Monitor Live Real-Time (Filtro Tiri attivi)</h2>
                            <table>
                                <thead>
                                    <tr>
                                        <th style="width: 15%; text-align:center;">Minuto</th>
                                        <th style="width: 42%;">Incontro / Competizione</th>
                                        <th style="width: 15%; text-align:center;">Tiri Porta</th>
                                        <th style="width: 28%;">Suggerimento Algoritmo</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {righe_live}
                                </tbody>
                            </table>
                        </div>
                        
                        <!-- SEZIONE PREMATCH -->
                        <div class="panel">
                            <h2 class="future-title">⏳ Palinsesto Prossime Ore (Studio Preventivo)</h2>
                            <table>
                                <thead>
                                    <tr>
                                        <th style="width: 20%; text-align:center;">Inizio</th>
                                        <th style="width: 45%;">Match / Campionato</th>
                                        <th style="width: 35%;">Analisi Statistica Archivio</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {righe_future}
                                </tbody>
                            </table>
                        </div>
                        
                    </div>
                </div>
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
# LOGICHE DI ANALISI AVANZATA (STORICO + TEMPO + LIVE)
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
                
                if campionato in DIZIONARIO_CAMPIONATI and timestamp_inizio > 0:
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

# =======================================================
# LOOP DI AVVIO
# =======================================================
if __name__ == "__main__":
    Thread(target=finto_server, daemon=True).start()
    print("Millenium Bot attivo! Monitor Live + Pre-Match pronto.", flush=True)
    
    while True:
        scansione_partite_live()
        scansione_prematch()
        time.sleep(60)
