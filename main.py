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
# VERA DASHBOARD WEB PER MONITORAGGIO SU PC
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
                righe_live = "<tr><td colspan='5' style='text-align:center; color:#8b949e;'>Nessun match live con tiri significativi rilevato.</td></tr>"
            else:
                for m in DASHBOARD_DATA["match_rilevanti"]:
                    righe_live += f"""
                    <tr>
                        <td><b>{m['orario']}</b></td>
                        <td style='color:#58a6ff;'><b>{m['partita']}</b><br><small style='color:#ffa198;'>Risultato: {m['punteggio']}</small></td>
                        <td><span style='background:#21262d; padding:2px 6px; border-radius:4px;'>{m['campionato']}</span></td>
                        <td style='color:#56d364; font-weight:bold;'>{m['tiri']}</td>
                        <td style='font-size:12px; white-space:pre-line;'>{m['analisi']}</td>
                    </tr>
                    """

            # 2. Costruzione tabella MATCH FUTURI
            righe_future = ""
            if not DASHBOARD_DATA["match_futuri"]:
                righe_future = "<tr><td colspan='4' style='text-align:center; color:#8b949e;'>Nessun match in programma nelle prossime ore per i campionati in archivio.</td></tr>"
            else:
                for mf in DASHBOARD_DATA["match_futuri"]:
                    righe_future += f"""
                    <tr>
                        <td style='color:#ffa198;'><b>{mf['data_ora']}</b></td>
                        <td><b>{mf['partita']}</b></td>
                        <td><span style='background:#21262d; padding:2px 6px; border-radius:4px;'>{mf['campionato']}</span></td>
                        <td style='font-size:12px; white-space:pre-line;'>{mf['analisi']}</td>
                    </tr>
                    """

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Millenium Bot - Monitor Avanzato</title>
                <meta http-equiv="refresh" content="30">
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #0d1117; color: #c9d1d9; margin:0; padding:20px; }}
                    .container {{ max-width: 1200px; margin: 0 auto; }}
                    .header {{ background: linear-gradient(135deg, #1f2937, #111827); padding: 20px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 25px; }}
                    h1 {{ color: #58a6ff; margin: 0 0 10px 0; font-size: 24px; }}
                    .status-bar {{ display: flex; gap: 20px; font-size: 14px; color: #8b949e; }}
                    .badge {{ background-color: rgba(56, 139, 253, 0.15); color: #58a6ff; padding: 4px 8px; border-radius: 6px; border: 1px solid rgba(56, 139, 253, 0.4); font-weight: bold; }}
                    .badge-online {{ background-color: rgba(53, 222, 101, 0.15); color: #56d364; border: 1px solid rgba(53, 222, 101, 0.4); }}
                    h2 {{ color: #58a6ff; font-size: 18px; border-left: 4px solid #1f6feb; padding-left: 10px; margin-top: 30px; margin-bottom: 10px; }}
                    h2.future-title {{ color: #ffa198; border-left: 4px solid #f85149; }}
                    table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; background-color: #161b22; border-radius: 8px; overflow: hidden; border: 1px solid #30363d; }}
                    th {{ background-color: #21262d; color: #58a6ff; text-align: left; padding: 12px; border-bottom: 1px solid #30363d; font-size: 13px; }}
                    td {{ padding: 12px; border-bottom: 1px solid #30363d; font-size: 13px; }}
                    tr:hover td {{ background-color: #1f242c; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🖥️ Centro Controllo Millenium Bot</h1>
                        <div class="status-bar">
                            <span>Radar: <span class="badge badge-online">🟢 ONLINE</span></span>
                            <span>Match nel Palinsesto Live: <span class="badge">{DASHBOARD_DATA["partite_scansionate"]}</span></span>
                            <span>Ultimo Screening: <span class="badge">{DASHBOARD_DATA["ultimo_aggiornamento"]}</span></span>
                        </div>
                    </div>
                    
                    <h2>🔥 1. Partite in Corso (LIVE con analisi andamento e minuto)</h2>
                    <table>
                        <thead>
                            <tr>
                                <th style="width: 10%;">Minuto</th>
                                <th style="width: 25%;">Partita / Risultato</th>
                                <th style="width: 25%;">Campionato</th>
                                <th style="width: 15%;">Tiri in Porta</th>
                                <th style="width: 25%;">Analisi Dinamica Live</th>
                            </tr>
                        </thead>
                        <tbody>
                            {righe_live}
                        </tbody>
                    </table>

                    <h2 class="future-title">📅 2. Palinsesto Prossime Ore (Pre-Match con studio automatico)</h2>
                    <table>
                        <thead>
                            <tr>
                                <th style="width: 15%;">Data e Ora Inizio</th>
                                <th style="width: 30%;">Partita (Club)</th>
                                <th style="width: 30%;">Campionato</th>
                                <th style="width: 25%;">Studio Preventivo Match</th>
                            </tr>
                        </thead>
                        <tbody>
                            {righe_future}
                        </tbody>
                    </table>
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
            
            # SEZIONE 1: LOGICA DINAMICA PER PARTITE IN CORSO (LIVE)
            if is_live and minuto is not None:
                output += f"⏱️ Analisi al minuto {minuto}' (Punteggio con {gol_totali} Gol):\n"
                
                if somma_medie >= 2.40:
                    if minuto <= 35:
                        output += "💰 <b>CONSIGLIO: OVER 0.5 HT (Entra se quota > 1.70)</b>"
                    elif minuto > 35 and minuto <= 65:
                        output += f"💰 <b>CONSIGLIO: OVER {gol_totali + 1.5} LIVE (Entra se quota > 1.80)</b>"
                    elif minuto > 65 and minuto <= 82:
                        output += f"💰 <b>CONSIGLIO: OVER {gol_totali + 0.5} FINALE (Pressione ultimi minuti)</b>"
                    else:
                        output += "⚠️ <i>CONSIGLIO: No Bet (Troppo tardi)</i>"
                else:
                    output += "⚠️ <i>CONSIGLIO: No Bet (Storico debole per gol live)</i>"
            
            # SEZIONE 2: LOGICA PER PARTITE FUTURE (PRE-MATCH)
            else:
                if somma_medie >= 3.20:
                    output += "💰 <b>STUDIO: Forte pendenza OVER 2.5</b>"
                elif somma_medie >= 2.40:
                    output += "💰 <b>STUDIO: Ottimo per OVER 1.5 Pre-Match</b>"
                elif somma_medie > 0:
                    output += "⚠️ <i>STUDIO: Match da Under o No Bet</i>"
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
                    # Chiamata pre-match (senza minuto e is_live=False)
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
                    
                    # 1. Recupero Info di Tempo e Punteggio Corrente dell'API
                    sc_data = partita.get("SC", {})
                    tempo_secondi = sc_data.get("TS", 0)
                    minuto_corrente = int(tempo_secondi // 60) if tempo_secondi > 0 else 1
                    
                    # Recupero Gol Attuali
                    gol_casa = int(sc_data.get("FS", {}).get("G1", 0))
                    gol_ospite = int(sc_data.get("FS", {}).get("G2", 0))
                    totale_gol_attuali = gol_casa + gol_ospite
                    stringa_punteggio = f"{gol_casa} - {gol_ospite}"
                    
                    # 2. Recupero Statistiche Tiri
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
                            "tiri": f"{tiri_totali_live} ({tiri_porta_casa}-{tiri_porta_ospite})",
                            "analisi": consiglio_live
                        })
                    
                    # SOGLIA TELEGRAM: SCATTA SOLO CON 5 TIRI O PIÙ
                    if tiri_totali_live >= 5:
                        consiglio_telegram = analizza_e_consiglia(
                            nome_file_csv, squadra_casa, squadra_ospite, 
                            minuto=minuto_corrente, gol_totali=totale_gol_attuali, is_live=True
                        )
                        # Pulizia tag grafici per Telegram
                        consiglio_text = consiglio_telegram.replace("<b>", "*").replace("</b>", "*").replace("<i>", "_").replace("</i>", "_")
                        
                        messaggio = (
                            f"*MILLENIUM BOT - COPERTURA LIVE VALUTATA*\n\n"
                            f"⚽ *Match:* {squadra_casa} - {squadra_ospite} ({stringa_punteggio})\n"
                            f"🏆 *Torneo:* {campionato_live}\n"
                            f"⏱️ *Minuto di Gioco:* {minuto_corrente}' minuto\n\n"
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
