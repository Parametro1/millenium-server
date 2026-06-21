import os
import time
import requests
import pandas as pd
from threading import Thread
import json
from http.server import SimpleHTTPRequestHandler
import socketserver

TOKEN = os.getenv("TELEGRAM_TOKEN", "INSERISCI_QUI_IL_TUO_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "INSERISCI_QUI_IL_TUO_CHAT_ID")
URL_LIVE = "https://1xlite-626219.top/LiveFeed/GetMatches30?sports=1&count=50&lng=it&cfv=0"
URL_FUTURE = "https://1xlite-626219.top/LineFeed/GetMatches30?sports=1&count=50&lng=it&cfv=0"
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

def invia_telegram(messaggio):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": messaggio, "parse_mode": "HTML"}
        requests.post(url, json=payload, timeout=10)
    except Exception:
        pass

def analizza_e_consiglia(nome_file_csv, casa, trasferta, minuto):
    try:
        file_standard = f"{nome_file_csv}.csv"
        file_maiuscolo = f"{nome_file_csv}.CSV"
        nome_file = file_standard if os.path.exists(file_standard) else file_maiuscolo
        if not os.path.exists(nome_file): return "Nessun CSV trovato."
        df = pd.read_csv(nome_file)
        df.columns = df.columns.str.strip()
        df_filtrato = df[((df['HomeTeam'] == casa) & (df['AwayTeam'] == trasferta)) | (df['HomeTeam'] == casa) | (df['AwayTeam'] == trasferta)]
        if df_filtrato.empty: return "Dati storici insufficienti. | No Bet"
        media_gol = (df_filtrato['FTHG'].mean() + df_filtrato['FTAG'].mean())
        media_casa = df_filtrato[df_filtrato['HomeTeam'] == casa]['FTHG'].mean()
        media_trasferta = df_filtrato[df_filtrato['AwayTeam'] == trasferta]['FTAG'].mean()
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
        return f"Errore analisi: {str(e)}"

def scansione_partite_live():
    global PARTITE_NOTIFICATE
    try:
        res = requests.get(URL_LIVE, timeout=15)
        if res.status_code != 200: return
        data = res.json()
        if not data.get("Value"): return
        for match in data["Value"]:
            campionato = match.get("LE", "")
            if campeonato not in DIZIONARIO_CAMPIONATI: continue
            match_id = str(match.get("I", ""))
            if match_id in PARTITE_NOTIFICATE: continue
            casa = match.get("O1", "")
            trasferta = match.get("O2", "")
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
            for s in statistiche:
                if s.get("T") == 1: tiri_totali = s.get("S1", 0) + s.get("S2", 0)
                if s.get("T") == 2: tiri_porta_totali = s.get("S1", 0) + s.get("S2", 0)
                if s.get("T") == 3: attacchi_pericolosi = s.get("S1", 0) + s.get("S2", 0)
            ap_minuto = attacchi_pericolosi / minuto if minuto > 0 else 0
            if (ap_minuto >= 1.15 and minuto >= 15 and tiri_totali >= 4) or (tiri_porta_totali >= 5):
                sigla_csv = DIZIONARIO_CAMPIONATI[campionato]
                consiglio = analizza_e_consiglia(sigla_csv, casa, trasferta, minuto)
                if "No Bet" not in consiglio and "Nessun CSV" not in consiglio:
                    msg = f"🔥 <b>MILLENIUM ATTACCO IN CORSO</b> 🔥\n\n<b>Match:</b> {casa} - {trasferta}\n<b>Minuto:</b> {minuto}' | <b>Score:</b> {g_casa}-{g_trasferta}\n\n<b>Tiri in Porta:</b> {tiri_porta_totali}\n<b>Pressione AP/Min:</b> {ap_minuto:.2f}\n\n<b>Analisi Storica:</b>\n{consiglio}"
                    invia_telegram(msg)
                    PARTITE_NOTIFICATE.add(match_id)
    except Exception:
        pass

def scansione_prematch():
    try:
        res = requests.get(URL_FUTURE, timeout=15)
        if res.status_code != 200: return
        data = res.json()
        if not data.get("Value"): return
        salva_dati = []
        for match in data["Value"]:
            campionato = match.get("LE", "")
            if campeonato not in DIZIONARIO_CAMPIONATI: continue
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
                html = "<html><body style='font-family:Arial;background:#1e1e2e;color:#cdd6f4;padding:40px;'><h1>📊 Millenium Bot Live Monitor</h1><p>Stato: ONLINE - Scansione attiva.</p></body></html>"
                self.wfile.write(html.encode("utf-8"))
            else: super().do_GET()
    port = int(os.environ.get("PORT", 10000))
    with socketserver.TCPServer(("", port), DashboardHandler) as httpd: httpd.serve_forever()

if __name__ == "__main__":
    print("Avvio del server web sulla porta impostata...", flush=True)
    Thread(target=avvia_server, daemon=True).start()
    time.sleep(5)
    print("Millenium Bot Pronto e Attivo!", flush=True)
    invia_telegram("✅ Il motore Millenium è ripartito ed è stabilizzato su Render!")
    while True:
        scansione_partite_live()
        scansione_prematch()
        time.sleep(60)
