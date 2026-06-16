from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import os
import time
import requests
import pandas as pd
from threading import Thread

# ==========================================
# CONFIGURAZIONI PRINCIPALI (Prese da Render)
# ==========================================
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
URL_LIVE = "https://1xbet.com/LiveFeed/GetMatchesVzip?sports=1&count=50&lng=it"

# Memoria globale temporanea per mostrare i dati sulla dashboard del PC
DASHBOARD_DATA = {
    "ultimo_aggiornamento": "Mai",
    "partite_scansionate": 0,
    "match_rilevanti": []
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
# VERA DASHBOARD WEB PER IL MONITORAGGIO SU PC
# =======================================================
class DashboardHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args): 
        return  # Non intasa i log di Render con le visite di UptimeRobot

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            
            # Generazione dinamica della tabella delle partite rilevanti
            righe_tabella = ""
            if not DASHBOARD_DATA["match_rilevanti"]:
                righe_tabella = "<tr><td colspan='5' style='text-align:center; color:#8b949e;'>Nessun match con tiri significativi rilevato in questo momento.</td></tr>"
            else:
                for m in DASHBOARD_DATA["match_rilevanti"]:
                    righe_tabella += f"""
                    <tr>
                        <td><b>{m['orario']}</b></td>
                        <td style='color:#58a6ff;'><b>{m['partita']}</b></td>
                        <td><span style='background:#21262d; padding:2px 6px; border-radius:4px;'>{m['campionato']}</span></td>
                        <td style='color:#56d364; font-weight:bold;'>{m['tiri']}</td>
                        <td style='font-size:11px; max-width:250px; white-space:pre-line;'>{m['analisi']}</td>
                    </tr>
                    """

            # Pagina Grafica stile Dark Professionale
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Millenium Bot - Centro Analisi Live</title>
                <meta http-equiv="refresh" content="30">
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #0d1117; color: #c9d1d9; margin:0; padding:20px; }}
                    .container {{ max-width: 1100px; margin: 0 auto; }}
                    .header {{ background: linear-gradient(135deg, #1f2937, #111827); padding: 20px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 20px; }}
                    h1 {{ color: #58a6ff; margin: 0 0 10px 0; font-size: 24px; }}
                    .status-bar {{ display: flex; gap: 20px; font-size: 14px; color: #8b949e; }}
                    .badge {{ background-color: rgba(56, 139, 253, 0.15); color: #58a6ff; padding: 4px 8px; border-radius: 6px; border: 1px solid rgba(56, 139, 253, 0.4); font-weight: bold; }}
                    .badge-online {{ background-color: rgba(53, 222, 101, 0.15); color: #56d364; border: 1px solid rgba(53, 222, 101, 0.4); }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background-color: #161b22; border-radius: 8px; overflow: hidden; border: 1px solid #30363d; }}
                    th {{ background-color: #21262d; color: #58a6ff; text-align: left; padding: 12px; border-bottom: 1px solid #30363d; }}
                    td {{ padding: 12px; border-bottom: 1px solid #30363d; font-size: 14px; }}
                    tr:hover td {{ background-color: #1f242c; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🖥️ Centro Controllo Millenium Bot</h1>
                        <div class="status-bar">
                            <span>Stato Radar: <span class="badge badge-online">🟢 ONLINE (UP)</span></span>
                            <span>Match nel Palinsesto Live: <span class="badge">{DASHBOARD_DATA["partite_scansionate"]}</span></span>
                            <span>Ultimo Screening: <span class="badge">{DASHBOARD_DATA["ultimo_aggiornamento"]}</span></span>
                        </div>
                    </div>
                    <h2>📊 Analisi Squadre in Archivio sotto Osservazione</h2>
                    <table>
                        <thead>
                            <tr>
                                <th style="width: 10%;">Orario</th>
                                <th style="width: 25%;">Partita (Club)</th>
                                <th style="width: 25%;">Campionato</th>
                                <th style="width: 15%;">Tiri in Porta Totali</th>
                                <th style="width: 25%;">Analisi Archivio Storico</th>
                            </tr>
                        </thead>
                        <tbody>
                            {righe_tabella}
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
    except Exception as e:
        print(f"Errore Server Web: {e}", flush=True)

# =======================================================
# FUNZIONI DEL BOT
# =======================================================
def invia_telegram(messaggio):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": messaggio, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Errore invio Telegram: {e}", flush=True)

def analizza_archivio_storico(nome_file_csv, casa_live, ospite_live):
    file_standard = f"{nome_file_csv}.csv"
    file_maiuscolo = f"{nome_file_csv}.CSV"
    nome_file = file_standard if os.path.exists(file_standard) else file_maiuscolo
    
    try:
        if os.path.exists(nome_file):
            df = pd.read_csv(nome_file)
            
            # Filtriamo i match storici usando la corrispondenza delle stringhe
            partite_casa = df[df['HomeTeam'].str.contains(casa_live, case=False, na=False)]
            partite_ospite = df[df['AwayTeam'].str.contains(ospite_live, case=False, na=False)]
            
            output = ""
            
            # Calcolo media gol fatti in casa (FTHG)
            if not partite_casa.empty and 'FTHG' in df.columns:
                media_fatti_casa = partite_casa['FTHG'].mean()
                output += f"🏠 Media Gol Fatti Casa: {media_fatti_casa:.2f}\n"
            else:
                output += f"🏠 Dati casa insufficienti.\n"
                
            # Calcolo media gol fatti in trasferta (FTAG)
            if not partite_ospite.empty and 'FTAG' in df.columns:
                media_fatti_ospite = partite_ospite['FTAG'].mean()
                output += f"🚀 Media Gol Fatti Fuori: {media_fatti_ospite:.2f}"
            else:
                output += f"🚀 Dati fuori casa insufficienti."
                
            return output
        else:
            return f"File {nome_file} non trovato."
    except Exception as e:
        return f"Errore calcolo: {str(e)}"

# =======================================================
# FUNZIONE PRINCIPALE DI SCANSIONE LIVE
# =======================================================
def scansione_partite():
    print("Scansione partite live in corso...", flush=True)
    try:
        response = requests.get(URL_LIVE, timeout=10)
        if response.status_code == 200:
            dati = response.json()
            partite = dati.get("Value", [])
            
            # Aggiorna contatori generali per la dashboard su PC
            DASHBOARD_DATA["partite_scansionate"] = len(partite)
            DASHBOARD_DATA["ultimo_aggiornamento"] = time.strftime("%H:%M:%S")
            
            nuovi_match_rilevanti = []
            
            for partita in partite:
                campionato_live = partita.get("L", "")
                squadra_casa = partita.get("O1", "")
                squadra_ospite = partita.get("O2", "")
                
                if campionato_live in DIZIONARIO_CAMPIONATI:
                    nome_file_csv = DIZIONARIO_CAMPIONATI[campionato_live]
                    
                    # Recupero dati dei tiri live dalle statistiche di 1xbet
                    stats = partita.get("SC", {}).get("S", [])
                    tiri_porta_casa = 0
                    tiri_porta_ospite = 0
                    
                    for stat in stats:
                        if stat.get("T") == 2:  # Tipo 2 = Tiri in porta totali
                            tiri_porta_casa = int(stat.get("G1", 0))
                            tiri_porta_ospite = int(stat.get("G2", 0))
                            break
                    
                    tiri_totali_live = tiri_porta_casa + tiri_porta_ospite
                    
                    # Se ci sono tiri, lo mettiamo in dashboard sul PC (anche prima della soglia dei 5, per vederlo arrivare!)
                    if tiri_totali_live > 0:
                        analisi_breve = analizza_archivio_storico(nome_file_csv, squadra_casa, squadra_ospite)
                        nuovi_match_rilevanti.append({
                            "orario": time.strftime("%H:%M"),
                            "partita": f"{squadra_casa} - {squadra_ospite}",
                            "campionato": campionato_live,
                            "tiri": f"{tiri_totali_live} ({tiri_porta_casa}-{tiri_porta_ospite})",
                            "analisi": analisi_breve
                        })
                    
                    # Se scatta la soglia reale dei 5 tiri totali, invia a Telegram!
                    if tiri_totali_live >= 5:
                        analisi_storica = analizza_archivio_storico(nome_file_csv, squadra_casa, squadra_ospite)
                        
                        messaggio = (
                            f"*MILLENIUM BOT - SEGNALE VALUE BET*\n\n"
                            f"*Partita:* {squadra_casa} - {squadra_ospite}\n"
                            f"*Campionato:* {campionato_live}\n\n"
                            f"*DATI LIVE ATTUALI:*\n"
                            f"🎯 Tiri in porta totali: *{tiri_totali_live}* ({tiri_porta_casa} - {tiri_porta_ospite})\n\n"
                            f"📊 *Analisi Archivio Storico:*\n{analisi_storica}\n\n"
                            f"💰 *Verifica la quota sul tuo bookmaker!*"
                        )
                        
                        invia_telegram(messaggio)
                        print(f"Segnale inviato su Telegram per: {squadra_casa} - {squadra_ospite}", flush=True)
                        time.sleep(5)
            
            # Conserva i dati per mostrarli sul PC
            DASHBOARD_DATA["match_rilevanti"] = nuovi_match_rilevanti
                                
    except Exception as e:
        print(f"Errore durante lo screening live: {e}", flush=True)

# =======================================================
# BLOCCO DI AVVIO REALE DEL PROCESSO
# =======================================================
if __name__ == "__main__":
    # Avvia la vera Dashboard Web sul thread di Render
    Thread(target=finto_server, daemon=True).start()
    
    print("Millenium Bot avviato con Dashboard Integrata!", flush=True)
    
    while True:
        scansione_partite()
        time.sleep(60)
