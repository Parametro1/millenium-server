from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import os
import time
import requests
import pandas as pd
from threading import Thread

# ==========================================
# CONFIGURAZIONI PRINCIPALI
# ==========================================
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
URL_LIVE = "https://1xbet.com/LiveFeed/GetMatchesVzip?sports=1&count=50&lng=it"
URL_FUTURE = "https://1xbet.com/LineFeed/GetMatchesVzip?sports=1&count=50&lng=it"

# Memoria globale per la dashboard del PC
DASHBOARD_DATA = {
    "ultimo_aggiornamento": "Mai",
    "partite_scansionate": 0,
    "match_rilevanti": [],
    "match_futuri": []
}

# =======================================================
# DIZIONARIO COMPLETO DI TRADUZIONE DEI CAMPIONATI
# =======================================================
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
# DASHBOARD WEB PROFESSIONALE (STILE TRADING)
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
                righe_live = "<tr><td colspan='4' style='text-align:center; color:#6e7681; padding:30px;'>Nessun match live con tiri significativi rilevato.</td></tr>"
            else:
                for m in DASHBOARD_DATA["match_rilevanti"]:
                    righe_live += f"""
                    <tr>
                        <td style='text-align:center;'><span class='time-badge'>{m['orario']}</span></td>
                        <td>
                            <div class='match-team'>{m['partita']}</div>
                            <div class='score-badge'>Risultato: {m['punteggio']}</div>
                            <div class='league-text'>{m['campionato']}</div>
                        </td>
                        <td style='text-align:center; color:#3fb950; font-weight:bold; font-size:15px;'>{m['tiri']}</td>
                        <td class='analysis-cell'>{m['analisi']}</td>
                    </tr>
                    """

            # 2. Costruzione tabella MATCH FUTURI
            righe_future = ""
            if not DASHBOARD_DATA["match_futuri"]:
                righe_future = "<tr><td colspan='3' style='text-align:center; color:#6e7681; padding:30px;'>Nessun match in programma nelle prossime ore per i campionati in archivio.</td></tr>"
            else:
                for mf in DASHBOARD_DATA["match_futuri"]:
                    righe_future += f"""
                    <tr>
                        <td style='text-align:center;'><span class='time-badge future'>{mf['data_ora']}</span></td>
                        <td>
                            <div class='match-team'>{mf['partita']}</div>
                            <div class='league-text'>{mf['campionato']}</div>
                        </td>
                        <td class='analysis-cell'>{mf['analisi']}</td>
                    </tr>
                    """

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Millenium Bot - Pro Dashboard</title>
                <meta http-equiv="refresh" content="30">
                <style>
                    body {{ font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif; background-color: #0d1117; color: #c9d1d9; margin:0; padding:25px; }}
                    .container {{ max-width: 1600px; margin: 0 auto; }}
                    
                    /* Header Professionale */
                    .header {{ background: #161b22; padding: 20px 30px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }}
                    h1 {{ color: #f0f6fc; margin: 0; font-size: 22px; font-weight: 600; display: flex; align-items: center; gap: 10px; }}
                    .status-bar {{ display: flex; gap: 15px; align-items: center; }}
                    .badge {{ background: #21262d; color: #c9d1d9; padding: 6px 12px; border-radius: 6px; border: 1px solid #30363d; font-size: 13px; font-weight: 500; }}
                    .badge span {{ color: #58a6ff; font-weight: bold; }}
                    .badge-online {{ background: rgba(56, 139, 253, 0.1); color: #58a6ff; border-color: rgba(56, 139, 253, 0.3); animation: pulse 2s infinite; }}

                    /* Layout Bifronte (Due Colonne Side-by-Side) */
                    .dashboard-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 25px; }}
                    @media (max-width: 1100px) {{ .dashboard-grid {{ grid-template-columns: 1fr; }} }}
                    
                    .panel {{ background: #161b22; border-radius: 12px; border: 1px solid #30363d; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
                    h2 {{ font-size: 16px; font-weight: 600; margin-top: 0; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #21262d; display: flex; align-items: center; gap: 8px; }}
                    .live-title {{ color: #ff5252; }}
                    .future-title {{ color: #ffab40; }}
                    
                    /* Tabelle in Stile Card */
                    table {{ width: 100%; border-collapse: separate; border-spacing: 0; margin-bottom: 10px; }}
                    th {{ background-color: #21262d; color: #8b949e; text-align: left; padding: 12px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #30363d; }}
                    th:first-child {{ border-top-left-radius: 6px; }}
                    th:last-child {{ border-top-right-radius: 6px; }}
                    td {{ padding: 14px 12px; border-bottom: 1px solid #21262d; color: #c9d1d9; vertical-align: top; }}
                    tr:last-child td {{ border-bottom: none; }}
                    tr:hover td {{ background-color: #1f242c; }}
                    
                    /* Elementi di Dettaglio */
                    .time-badge {{ background: rgba(248, 81, 73, 0.1); color: #ff5252; padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 12px; border: 1px solid rgba(248, 81, 73, 0.2); display: inline-block; }}
                    .time-badge.future {{ background: rgba(255, 171, 64, 0.1); color: #ffab40; border: 1px solid rgba(255, 171, 64, 0.2); }}
                    .match-team {{ font-weight: 600; font-size: 14px; color: #f0f6fc; margin-bottom: 4px; }}
                    .score-badge {{ font-size: 11px; color: #ffa198; background: rgba(255, 161, 152, 0.05); padding: 2px 6px; border-radius: 4px; display: inline-block; margin-bottom: 4px; border: 1px solid rgba(255, 161, 152, 0.1); }}
                    .league-text {{ font-size: 11px; color: #8b949e; }}
                    .analysis-cell {{ font-size: 12px; color: #c9d1d9; line-height: 1.5; white-space: pre-line; }}
                    
                    /* Evidenziatori di Consigli */
                    b {{ color: #58a6ff; font-weight: 600; }}
                    i {{ color: #8b949e; font-style: italic; }}
                    
                    @keyframes pulse {{
                        0% {{ opacity: 0.8; }}
                        50% {{ opacity: 1; }}
                        100% {{ opacity: 0.8; }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>💻 Millenium Intelligence — Centro Controllo</h1>
                        <div class="status-bar">
                            <div class="badge badge-online">● RADAR LIVE ACCESO</div>
                            <div class="badge">Palinsesto: <span>{DASHBOARD_DATA["partite_scansionate"]}</span></div>
                            <div class="badge">Aggiornato: <span>{DASHBOARD_DATA["ultimo_aggiornamento"]}</span></div>
                        </div>
                    </div>
                    
                    <div class="dashboard-grid">
                        
                        <div class="panel">
                            <h2 class="live-title">🔥 Partite in Corso (Statistiche Real-Time)</h2>
                            <table>
                                <thead>
                                    <tr>
                                        <th style="width: 15%; text-align:center;">Minuto</th>
                                        <th style="width: 40%;">Squadre / Torneo</th>
                                        <th style="width: 15%; text-align:center;">Tiri Porta</th>
                                        <th style="width: 30%;">Consiglio Dinamico</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {righe_live}
                                </tbody>
                            </table>
                        </div>
                        
                        <div class="panel">
                            <h2 class="future-title">📅 Prossime Ore (Studio Preventivo Archivio)</h2>
                            <table>
                                <thead>
                                    <tr>
                                        <th style="width: 20%; text-align:center;">Calcio Inizio</th>
                                        <th style="width: 45%;">Squadre / Campionato</th>
                                        <th style="width: 35%;">Studio Algoritmo</th>
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
        response = requests.get(URL_FUTURE, timeout=10)
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
        response = requests.get(URL_LIVE, timeout=10)
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
# LOOP DI AVVIO REALE
# =======================================================
if __name__ == "__main__":
    Thread(target=finto_server, daemon=True).start()
    print("Millenium Bot attivo! Monitor Live (con Minuti e Gol) + Pre-Match pronto.", flush=True)
    
    while True:
        scansione_partite_live()
        scansione_prematch()
        time.sleep(60)
