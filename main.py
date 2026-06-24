import os
import time
import requests
import pandas as pd
from threading import Thread
import json
from http.server import SimpleHTTPRequestHandler
import socketserver
import re

# Manteniamo RIGOROSAMENTE le tue chiavi reali di Render
TOKEN = os.getenv("TELEGRAM_TOKEN", "INSERISCI_QUI_IL_TUO_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "INSERISCI_QUI_IL_TUO_CHAT_ID")
URL_LIVE = "https://1xbet.com/LiveFeed/GetMatches30?sports=1&count=50&lng=it&cfv=0"
URL_FUTURE = "https://1xbet.com/LineFeed/GetMatches30?sports=1&count=50&lng=it&cfv=0"
DATA_FILE = "dati_partite.json"

DIZIONARIO_CAMPIONATI = {
    "Calcio. Italia. Serie A": "I1", "Calcio. Italia. Serie B": "I2",
    "Calcio. Inghilterra. Premier League": "E0", "Calcio. Inghilterra. Championship": "E1",
    "Calcio. Spagna. Primera Division": "SP1", "Calcio. Germania. Bundesliga": "D1",
    "Calcio. Francia. Ligue 1": "F1", "Calcio. Olanda. Eredivisie": "N1",
    "Calcio. Portogallo. Primeira Liga": "P1", "Calcio. Belgio. Pro League": "B1",
    "Calcio. Turchia. Super Lig": "T1", "Calcio. Scozia. Premiership": "SC0",
    "Calcio. Danimarca. Superligaen": "DNK", "Calcio. Svizzera. Super League": "SWI",
    "Calcio. Austria. Bundesliga": "AUT", "Calcio. Grecia. Super League": "GRC",
    "Calcio. Croazia. HNL": "HRV", "Calcio. Repubblica Ceca. 1. Liga": "CZE",
    "Calcio. Romania. Liga I": "ROU", "Calcio. Polonia. Ekstraklasa": "POL",
    "Calcio. Svezia. Allsvenskan": "SWE", "Calcio. Norvegia. Eliteserien": "NOR",
    "Calcio. Finlandia. Veikkausliiga": "FIN", "Calcio. Irlanda. Premier Division": "IRL",
    "Calcio. Giappone. J1 League": "JPN", "Calcio. Messico. Liga MX": "MEX",
    "Calcio. Brasile. Serie A": "BRA", "Calcio. Argentina. Liga Profesional": "ARG"
}

PARTITE_NOTIFICATE = set()

def normalizza_nome(nome):
    if not isinstance(nome, str): return ""
    nome = nome.lower()
    nome = re.sub(r'[-–_]', ' ', nome)
    nome = re.sub(r'[áàâãä]', 'a', nome).replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    return " ".join(nome.split())

def match_squadre(nome_live, nome_csv):
    n_live = normalizza_nome(nome_live)
    n_csv = normalizza_nome(nome_csv)
    return (n_live in n_csv) or (n_csv in n_live)

def invia_telegram(messaggio):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": messaggio, "parse_mode": "HTML"}
        res = requests.post(url, json=payload, timeout=10)
        print(f"Risposta Telegram: {res.status_code} - {res.text}", flush=True)
    except Exception as e:
        print(f"Errore invio Telegram: {str(e)}", flush=True)

def analizza_e_consiglia(nome_file_csv, casa, trasferta, minuto):
    try:
        file_standard = f"{nome_file_csv}.csv"
        file_maiuscolo = f"{nome_file_csv}.CSV"
        nome_file = file_standard if os.path.exists(file_standard) else file_maiuscolo
        if not os.path.exists(nome_file): 
            print(f"⚠️ CSV Non Trovato per la sigla: {nome_file_csv}", flush=True)
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
            print(f"⚠️ [Mancata Corrispondenza Nomi] Live: {casa} - {trasferta} | CSV Trovati: Casa={casa_csv}, Fuori={trasferta_csv}", flush=True)
            return "Dati storici insufficienti. | No Bet"
            
        df_filtrato = df[((df[col_home] == casa_csv) & (df[col_away] == trasferta_csv)) | (df[col_home] == casa_csv) | (df[col_away] == trasferta_csv)]
        if df_filtrato.empty: return "Dati storici insufficienti. | No Bet"
        
        media_gol = (df_filtrato[col_hg].mean() + df_filtrato[col_ag].mean())
        media_casa = df_filtrato[df_filtrato[col_home] == casa_csv][col_hg].mean()
        media_trasferta = df_filtrato[df_filtrato[col_away] == trasferta_csv][col_ag].mean()
        
        if pd.isna(media_casa): media_casa = 0.0
        if pd.isna(media_trasferta): media_trasferta = 0.0
        if pd.isna(media_gol): media_gol = 0.0
        
        info_medie = f"Media: {media_gol:.2f} (C:{media_casa:.1f} F:{media_trasferta:.1f})"
        if media_gol >= 2.40:
            if minuto <= 35: return f"{info_medie} | OVER 0.5 HT"
            elif 36 <= minuto <= 65: return f"{info_medie} | OVER LIVE"
            elif 66 <= minuto <= 82: return f"{info_medie} | OVER 0.5 FINALE"
        return f"{info_medie} | No Bet"
    except Exception as e:
        print(f"❌ Errore critico in analizza_e_consiglia: {str(e)}", flush=True)
        return f"ErroreDoc: {str(e)}"

def scansione_partite_live():
    global PARTITE_NOTIFICATE
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        res = requests.get(URL_LIVE, headers=headers, timeout=15)
        if res.status_code not in [200, 203]: 
            print(f"⚠️ Server risponde con status {res.status_code}", flush=True)
            return
        data = res.json()
        if not data.get("Value"): return
        for match in data["Value"]:
            campionato = match.get("LE", "")
            if campionato not in DIZIONARIO_CAMPIONATI: continue
            match_id = str(match.get("I", ""))
            if match_id in PARTITE_NOTIFICATE: continue
            
            casa = match.get("O1E", match.get("O1", ""))
            trasferta = match.get("O2E", match.get("O2", ""))
            
            sc = match.get("SC", {})
            ts = sc.get("TS", 0)
            minuto = ts // 60
            fs = sc.get("FS", {})
            g_casa = fs.get("S1", 0)
            g_trasferta = fs.get("S2", 0)
            
            statistiche = sc.get("S", [])
            tiri_totali = 0
            tiri_porta_totali = 0
            attacchi_pericolosi = 0
            corner_totali = 0
            
            for s in statistiche:
                if s.get("T") == 1: tiri_totali = s.get("S1", 0) + s.get("S2", 0)
                if s.get("T") == 2: tiri_porta_totali = s.get("S1", 0) + s.get("S2", 0)
                if s.get("T") == 3: attacchi_pericolosi = s.get("S1", 0) + s.get("S2", 0)
                if s.get("T") == 4: corner_totali = s.get("S1", 0) + s.get("S2", 0)
                
            ap_minuto = attacchi_pericolosi / minuto if minuto > 0 else 0
            
            condizione_assedio = (ap_minuto >= 1.25 and minuto >= 15 and tiri_totali >= 5 and corner_totali >= 3)
            condizione_bombardamento = (tiri_porta_totali >= 5 and corner_totali >= 2)
            
            if condizione_assedio or condizione_bombardamento:
                sigla_csv = DIZIONARIO_CAMPIONATI[campionato]
                consiglio = analizza_e_consiglia(sigla_csv, casa, trasferta, minuto)
                if "No Bet" not in consiglio and "Nessun CSV" not in consiglio:
                    msg = (
                        f"🔥 <b>MILLENIUM: GOL IMMINENTE</b> 🔥\n\n"
                        f"<b>Match:</b> {casa} - {trasferta}\n"
                        f"<b>Minuto:</b> {minuto}' | <b>Score:</b> {g_casa}-{g_trasferta}\n\n"
                        f"<b>Calci d'Angolo:</b> {corner_totali} 📐\n"
                        f"<b>Tiri (In Porta / Tot):</b> {tiri_porta_totali} / {tiri_totali} ⚽\n"
                        f"<b>Pressione AP/Min:</b> {ap_minuto:.2f} ⚡\n\n"
                        f"<b>Analisi Storica:</b>\n{consiglio}"
                    )
                    invia_telegram(msg)
                    PARTITE_NOTIFICATE.add(match_id)
    except Exception as e:
        print(f"❌ Errore in scansione_partite_live: {str(e)}", flush=True)

def scansione_prematch():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*"
        }
        res = requests.get(URL_FUTURE, headers=headers, timeout=15)
        if res.status_code != 200: return
        data = res.json()
        if not data.get("Value"): return
        salva_dati = []
        for match in data["Value"]:
            campionato = match.get("LE", "")
            if campionato not in DIZIONARIO_CAMPIONATI: continue
            salva_dati.append({"id": match.get("I"), "home": match.get("O1"), "away": match.get("O2"), "league": campionato, "time": match.get("S")})
        with open(DATA_FILE, "w") as f: json.dump(salva_dati, f)
    except Exception:
        pass

def avvia_server():
    class DashboardHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/":
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                
                html = """<html>
                <head>
                    <title>Millenium Bot Dashboard</title>
                    <meta charset="utf-8">
                    <style>
                        body { font-family: 'Segoe UI', Arial, sans-serif; background-color: #1a1a24; color: #e2e8f0; margin: 0; padding: 40px; display: flex; justify-content: center; }
                        .container { max-width: 800px; width: 100%; }
                        h1 { color: #818cf8; font-size: 2.5rem; margin-bottom: 10px; display: flex; align-items: center; gap: 10px; }
                        .status-box { background: #242432; padding: 20px; border-radius: 12px; border-left: 6px solid #34d399; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2); margin-bottom: 25px; }
                        .status-title { font-size: 1.2rem; font-weight: bold; color: #34d399; margin-bottom: 5px; }
                        .info-card { background: #242432; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2); }
                        p { color: #94a3b8; line-height: 1.6; }
                        .badge { background: #065f46; color: #a7f3d0; padding: 4px 10px; border-radius: 6px; font-size: 0.9rem; font-weight: 500; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>📊 Millenium Live Core</h1>
                        <div class="status-box">
                            <div class="status-title">● MOTORE ATTIVO H24</div>
                            <p style="margin:0; color:#cbd5e1;">Il server sta scansionando i flussi live di 1XBet in tempo reale. Algoritmo avanzato con filtro Corner attivo.</p>
                        </div>
                        <div class="info-card">
                            <h3>⚙️ Informazioni di Sistema</h3>
                            <p><b>Connessione Telegram:</b> <span class="badge">ONLINE</span></p>
                            <p><b>Auto-Ping Anti Sonno:</b> Attivo ogni 10 minuti</p>
                            <p><b>Frequenza Scansione:</b> Ciclo continuo (60 secondi)</p>
                        </div>
                    </div>
                </body>
                </html>"""
                self.wfile.write(html.encode("utf-8"))
            else: super().do_GET()
    port = int(os.environ.get("PORT", 10000))
    with socketserver.TCPServer(("", port), DashboardHandler) as httpd: httpd.serve_forever()

def auto_ping_server():
    time.sleep(30)
    while True:
        try:
            url_server = f"http://localhost:{os.environ.get('PORT', 10000)}/"
            requests.get(url_server, timeout=10)
            print("🔄 Keep-Alive Ping inviato con successo. Server sveglio.", flush=True)
        except Exception:
            pass
        time.sleep(600)

if __name__ == "__main__":
    print("Avvio del server web sulla porta impostata...", flush=True)
    Thread(target=avvia_server, daemon=True).start()
    Thread(target=auto_ping_server, daemon=True).start()
    
    time.sleep(5)
    print("Millenium Bot Pronto e Attivo con Normalizzazione Nomi e Colonne!", flush=True)
    invia_telegram("Il motore Millenium e aggiornato con filtro Corner h24 e Auto-Normalizzazione!")
    
    while True:
        try:
            scansione_partite_live()
            scansione_prematch()
        except Exception as e:
            print(f"⚠️ Errore temporaneo nel ciclo: {str(e)}. Il bot continua a scansionare...", flush=True)
        time.sleep(60)
