import os
import time
import requests
import pandas as pd
from threading import Thread
import json
from http.server import SimpleHTTPRequestHandler
import socketserver
import re

# Chiavi recuperate in automatico dalle Environment Variables di Render
TOKEN = os.getenv("TELEGRAM_TOKEN", "INSERISCI_QUI_IL_TUO_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "INSERISCI_QUI_IL_TUO_CHAT_ID")

# Endpoint Gateway pubblico e ottimizzato per Bet365 Live (No Blocchi Cloudflare su Render)
URL_BET365_LIVE = "https://b365-api-v2.vercel.app/api/live" 
DATA_FILE = "dati_partite.json"

# Dizionario aggiornato con la nomenclatura ufficiale internazionale di Bet365
DIZIONARIO_CAMPIONATI = {
    "Italy Serie A": "I1", "Italy Serie B": "I2",
    "England Premier League": "E0", "England Championship": "E1",
    "Spain Primera Liga": "SP1", "Germany Bundesliga": "D1",
    "France Ligue 1": "F1", "Netherlands Eredivisie": "N1",
    "Portugal Primeira Liga": "P1", "Belgium First Division A": "B1",
    "Turkey Super Lig": "T1", "Scotland Premiership": "SC0",
    "Denmark Superliga": "DNK", "Switzerland Super League": "SWI",
    "Austria Bundesliga": "AUT", "Greece Super League": "GRC",
    "Croatia HNL": "HRV", "Czech Republic First League": "CZE",
    "Romania Liga I": "ROU", "Poland Ekstraklasa": "POL",
    "Sweden Allsvenskan": "SWE", "Norway Eliteserien": "NOR",
    "Finland Veikkausliiga": "FIN", "Republic of Ireland Premier Division": "IRL",
    "Japan J1 League": "JPN", "Mexico Liga MX": "MEX",
    "Brazil Serie A": "BRA", "Argentina Liga Profesional": "ARG"
}

PARTITE_NOTIFICATE = set()

def normalizza_nome(nome):
    if not isinstance(nome, str): return ""
    nome = nome.lower()
    rimuovere = ["fc", "cf", "ud", "ac", "ssc", "rc", "as", "sv", "fk", "cd", "atletico", "club"]
    for parola in rimuovere:
        nome = re.sub(r'\b' + parola + r'\b', '', nome)
    nome = re.sub(r'[-–_]', ' ', nome)
    nome = re.sub(r'[áàâãä]', 'a', nome).replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    return " ".join(nome.split())

def match_squadre(nome_live, nome_csv):
    n_live = normalizza_nome(nome_live)
    n_csv = normalizza_nome(nome_csv)
    if not n_live or not n_csv: return False
    return (n_live in n_csv) or (n_csv in n_live) or (n_live[:4] == n_csv[:4])

def invia_telegram(messaggio):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": messaggio, "parse_mode": "HTML"}
        res = requests.post(url, json=payload, timeout=10)
        print(f"Risposta Telegram: {res.status_code}", flush=True)
    except Exception as e:
        print(f"Errore invio Telegram: {str(e)}", flush=True)

def analizza_e_consiglia(nome_file_csv, casa, trasferta, minuto):
    try:
        file_standard = f"{nome_file_csv}.csv"
        file_maiuscolo = f"{nome_file_csv}.CSV"
        nome_file = file_standard if os.path.exists(file_standard) else file_maiuscolo
        if not os.path.exists(nome_file): 
            return "Nessun CSV trovato."
            
        df = pd.read_csv(nome_file)
        df.columns = df.columns.str.strip()
        
        col_home = 'Home' if 'Home' in df.columns else 'HomeTeam'
        col_away = 'Away' if 'Away' in df.columns else 'AwayTeam'
        col_hg = 'HG' if 'HG' in df.columns else 'FTHG'
        col_ag = 'AG' if 'AG' in df.columns else 'FTAG'
        
        casa_csv = None
        trasferta_csv = None
        
        for squad_csv in df[col_home].unique():
            if match_squadre(casa, squad_csv):
                casa_csv = squad_csv
                break
        for squad_csv in df[col_away].unique():
            if match_squadre(trasferta, squad_csv):
                trasferta_csv = squad_csv
                break
                
        if not casa_csv or not trasferta_csv:
            print(f"⚠️ [Nomi non allineati] Live: {casa}-{trasferta} | CSV: {casa_csv}-{trasferta_csv}", flush=True)
            return "Dati storici insufficienti. | No Bet"
            
        df_filtrato = df[((df[col_home] == casa_csv) & (df[col_away] == trasferta_csv)) | (df[col_home] == casa_csv) | (df[col_away] == trasferta_csv)]
        if df_filtrato.empty: return "Dati storici insufficienti. | No Bet"
        
        media_gol = (df_filtrato[col_hg].mean() + df_filtrato[col_ag].mean())
        media_casa = df_filtrato[df_filtrato[col_home] == casa_csv][col_hg].mean()
        media_trasferta = df_filtrato[df_filtrato[col_away] == trasferta_csv][col_ag].mean()
        
        if pd.isna(media_casa): media_casa = 0.0
        if pd.isna(media_trasferta): media_trasferta = 0.0
        if pd.isna(media_gol): media_gol = 0.0
        
        info_medie = f"Media Gol Storica: {media_gol:.2f} (C:{media_casa:.1f} F:{media_trasferta:.1f})"
        if media_gol >= 2.40:
            if minuto <= 35: return f"{info_medie} | OVER 0.5 HT"
            elif 36 <= minuto <= 65: return f"{info_medie} | OVER LIVE"
            elif 66 <= minuto <= 82: return f"{info_medie} | OVER 0.5 FINALE"
        return f"{info_medie} | No Bet"
    except Exception as e:
        return f"Errore Analisi: {str(e)}"

def scansione_partite_live():
    global PARTITE_NOTIFICATE
    try:
        print("🔄 Avvio scansione partite live da Bet365...", flush=True)
        res = requests.get(URL_BET365_LIVE, timeout=15)
        if res.status_code != 200: return
        
        data = res.json()
        if not data or "games" not in data: return
        
        for game in data["games"]:
            campionato = game.get("league", "")
            if campionato not in DIZIONARIO_CAMPIONATI: continue
            
            game_id = str(game.get("id", ""))
            if game_id in PARTITE_NOTIFICATE: continue
            
            casa = game.get("home_team", "")
            trasferta = game.get("away_team", "")
            minuto = int(game.get("minute", 0))
            
            g_casa = int(game.get("home_score", 0))
            g_trasferta = int(game.get("away_score", 0))
            
            stats = game.get("stats", {})
            tiri_porta_totali = int(stats.get("on_target_home", 0)) + int(stats.get("on_target_away", 0))
            tiri_fuori_totali = int(stats.get("off_target_home", 0)) + int(stats.get("off_target_away", 0))
            tiri_totali = tiri_porta_totali + tiri_fuori_totali
            
            attacchi_pericolosi = int(stats.get("dangerous_attacks_home", 0)) + int(stats.get("dangerous_attacks_away", 0))
            corner_totali = int(stats.get("corners_home", 0)) + int(stats.get("corners_away", 0))
            
            ap_minuto = attacchi_pericolosi / minuto if minuto > 0 else 0
            
           condizione_assedio = (ap_minuto >= 0.50 and minuto >= 10 and tiri_totali >= 3 and corner_totali >= 2)
            condizione_bombardamento = (tiri_porta_totali >= 5 and corner_totali >= 2)
            
            if condizione_assedio or condizione_bombardamento:
                sigla_csv = DIZIONARIO_CAMPIONATI[campionato]
                consiglio = analizza_e_consiglia(sigla_csv, casa, trasferta, minuto)
                
                if "No Bet" not in consiglio and "Nessun CSV" not in consiglio:
                    msg = (
                        f"🔥 <b>MILLENIUM: GOL IMMINENTE (B365)</b> 🔥\n\n"
                        f"<b>Match:</b> {casa} - {trasferta}\n"
                        f"<b>Competizione:</b> {campionato}\n"
                        f"<b>Minuto:</b> {minuto}' | <b>Score:</b> {g_casa}-{g_trasferta}\n\n"
                        f"<b>Calci d'Angolo:</b> {corner_totali} 📐\n"
                        f"<b>Tiri (In Porta / Tot):</b> {tiri_porta_totali} / {tiri_totali} ⚽\n"
                        f"<b>Pressione AP/Min:</b> {ap_minuto:.2f} ⚡\n\n"
                        f"<b>Analisi Storica:</b>\n{consiglio}"
                    )
                    invia_telegram(msg)
                    PARTITE_NOTIFICATE.add(game_id)
    except Exception as e:
        print(f"⚠️ Errore lettura feed: {str(e)}", flush=True)

def avvia_server():
    class DashboardHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/":
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                html = "<html><body style='background:#121214;color:#fff;font-family:sans-serif;padding:40px;'><h1>📊 Millenium Core v365 Attivo</h1><p>Scansione flussi real-time ottimizzata per hosting Render.</p></body></html>"
                self.wfile.write(html.encode("utf-8"))
            else: super().do_GET()
    port = int(os.environ.get("PORT", 10000))
    with socketserver.TCPServer(("", port), DashboardHandler) as httpd: httpd.serve_forever()

if __name__ == "__main__":
    print("Avvio server di monitoraggio web...", flush=True)
    Thread(target=avvia_server, daemon=True).start()
    
    time.sleep(2)
    print("Millenium Bot Pronto con Database Bet365 Core!", flush=True)
    invia_telegram("Il motore Millenium è ONLINE h24 su Render (Feed Bet365 ad altissima stabilità)!")
    
    while True:
        try:
            scansione_partite_live()
        except Exception as e:
            pass
        time.sleep(60)
