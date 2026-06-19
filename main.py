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
adapter = requests.adapters.HTTPAdapter(max_retries=2)
session.mount("https://", adapter)

# Inizializzazione del dizionario dati per la Dashboard
DASHBOARD_DATA = {
    "ultimo_aggiornamento": "Mai",
    "partite_scansionate": 0,
    "alert_inviati_totale": 0,
    "match_rilevanti": [],
    "match_futuri": []
}

if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            DASHBOARD_DATA = json.load(f)
    except Exception:
        pass

DIZIONARIO_CAMPIONATI = {
    "Calcio. Inghilterra. Premier League": "E0", "Calcio. Inghilterra. Championship": "E1",
    "Calcio. Inghilterra. League One": "E2", "Calcio. Inghilterra. League Two": "E3",
    "Calcio. Inghilterra. National League": "EC", "Calcio. Germania. Bundesliga": "D1",
    "Calcio. Germania. 2. Bundesliga": "D2", "Calcio. Germania. 3. Liga": "D3",
    "Calcio. Italia. Serie A": "I1", "Calcio. Italia. Serie B": "I2",
    "Calcio. Spagna. Primera Division": "SP1", "Calcio. Spagna. Segunda Division": "SP2",
    "Calcio. Francia. Ligue 1": "F1", "Calcio. Francia. Ligue 2": "F2",
    "Calcio. Olanda. Eredivisie": "N1", "Calcio. Olanda. Eerste Divisie": "N2",
    "Calcio. Portogallo. Primeira Liga": "P1", "Calcio. Turchia. SuperLig": "T1",
    "Calcio. Belgio. Pro League": "B1", "Calcio. Scozia. Premiership": "SC0",
    "Calcio. Scozia. Championship": "SC1", "Calcio. Grecia. Super League": "G1",
    "Calcio. Austria. Bundesliga": "A1", "Calcio. Svizzera. Super League": "SW1",
    "Calcio. Danimarca. Superligaen": "DN1", "Calcio. Norvegia. Eliteserien": "N1",
    "Calcio. Svezia. Allsvenskan": "S1", "Calcio. USA. MLS": "USA"
}

def salva_dati_su_file():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(DASHBOARD_DATA, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Errore scrittura JSON: {e}", flush=True)

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
            
            # Interfaccia pulita senza righe multilinea lunghe soggette a errori di codifica
            res = "<html><head><title>Terminal</title></head><body style='font-family:sans-serif; background:#0d1117; color:#c9d1d9; padding:20px;'>"
            res += "<h1>⚡ Millenium Monitoring Terminal ⚡</h1>"
            res += f"<p><b>Ultimo Aggiornamento:</b> {DASHBOARD_DATA['ultimo_aggiornamento']}</p>"
            res += f"<p><b>Partite Scansionate Live:</b> {DASHBOARD_DATA['partite_scansionate']}</p>"
            res += f"<p><b>Alert Inviati Telegram:</b> {DASHBOARD_DATA['alert_inviati_totale']}</p>"
            res += "<h2>Match Live Monitorati</h2><ul>"
            
            if not DASHBOARD_DATA["match_rilevanti"]:
                res += "<li>Nessun match attivo soddisfa i criteri minimi in questo istante.</li>"
            else:
                for m in DASHBOARD_DATA["match_rilevanti"]:
                    res += f"<li><b>{m['partita']}</b> ({m['orario']}) - Punteggio: {m['punteggio']}<br>{m['analisi']}</li>"
            
            res += "<h2>Palinsesto Prematch Analizzato</h2><ul>"
            if not DASHBOARD_DATA.get("match_futuri"):
                res += "<li>Nessun match futuro in archivio.</li>"
            else:
                for mf in DASHBOARD_DATA["match_futuri"]:
                    res += f"<li>[{mf['data_ora']}] <b>{mf['partita']}</b> - <i>{mf['campionato']}</i><br>{mf['analisi']}</li>"
                    
            res += "</ul><script>setTimeout(function(){ location.reload(); }, 15000);</script></body></html>"
            self.wfile.write(res.encode("utf-8"))
        else:
            self.send_error(404, "Not Found")

def avvia_server():
    porta = int(os.environ.get("PORT", 10000))
    print(f"Avvio server HTTP sulla porta {porta}...", flush=True)
    try:
        with TCPServer(("0.0.0.0", porta), DashboardHandler) as server:
            server.serve_forever()
    except Exception as e:
        print(f"Errore Server: {e}", flush=True)

# =======================================================
# LOGICHE DI ANALISI STATISTICA STORICA
# =======================================================
def analizza_e_consiglia(nome_file_csv, casa_live, ospite_live, minuto=None, gol_totali=0, is_live=False):
    file_standard = f"{nome_file_csv}.csv"
    file_maiuscolo = f"{nome_file_csv}.CSV"
    nome_file = file_standard if os.path.exists(file_standard) else file_maiuscolo
    
    if not os.path.exists(nome_file):
        return "Nessun dato d'archivio CSV disponibile per questa lega."
        
    try:
        df = pd.read_csv(nome_file)
        partite_casa = df[df['HomeTeam'].str.contains(casa_live, case=False, na=False)]
        partite_ospite = df[df['AwayTeam'].str.contains(ospite_live, case=False, na=False)]
        
        media_casa = float(partite_casa['FTHG'].mean()) if not partite_casa.empty and 'FTHG' in df.columns else 0.0
        media_fuori = float(partite_ospite['FTAG'].mean()) if not partite_ospite.empty and 'FTAG' in df.columns else 0.0
        somma_medie = media_casa + media_fuori
        
        output = f"Media Storica Casa: {media_casa:.2f} | Fuori: {media_fuori:.2f} | "
        
        if is_live and minuto is not None:
            if somma_medie >= 2.40:
                if minuto <= 35: output += "CONSIGLIO: OVER 0.5 HT"
                elif minuto <= 65: output += f"CONSIGLIO: OVER {gol_totali + 1.5} LIVE"
                elif minuto <= 82: output += f"CONSIGLIO: OVER {gol_totali + 0.5} FINALE"
                else: output += "No Bet"
            else:
                output += "No Bet (Media bassa)"
        else:
            if somma_medie >= 3.20: output += "STUDIO: Segno OVER 2.5"
            elif somma_medie >= 2.40: output += "STUDIO: Segno OVER 1.5"
            else: output += "STUDIO: Segno UNDER"
        return output
    except Exception:
        return "Errore durante l'elaborazione del file CSV."

# =======================================================
# ENGINE DI SCANSIONE DATI API
# =======================================================
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
                
                if campionato_live in DIZIONARIO_CAMPIONATI:
                    nome_file_csv = DIZIONARIO_CAMPIONATI[campionato_live]
                    sc_data = partita.get("SC", {})
                    tempo_secondi = sc_data.get("TS", 0)
                    minuto_corrente = int(tempo_secondi // 60) if tempo_secondi > 0 else 1
                    
                    fs_data = sc_data.get("FS", {})
                    gol_casa = int(fs_data.get("G1", 0))
                    gol_ospite = int(fs_data.get("G2", 0))
                    totale_gol_attuali = gol_casa + gol_ospite
                    
                    tiri_porta_casa, tiri_porta_ospite = 0, 0
                    tiri_fuori_casa, tiri_fuori_ospite = 0, 0
                    ap_casa, ap_ospite = 0, 0
                    
                    for stat in sc_data.get("S", []):
                        tipo_stat = stat.get("T")
                        if tipo_stat == 2:
                            tiri_porta_casa, tiri_porta_ospite = int(stat.get("G1", 0)), int(stat.get("G2", 0))
                        elif tipo_stat == 1:
                            tiri_fuori_casa, tiri_fuori_ospite = int(stat.get("G1", 0)), int(stat.get("G2", 0))
                        elif tipo_stat == 3:
                            ap_casa, ap_ospite = int(stat.get("G1", 0)), int(stat.get("G2", 0))
                    
                    tiri_porta_totali = tiri_porta_casa + tiri_porta_ospite
                    tiri_totali = tiri_porta_totali + tiri_fuori_casa + tiri_fuori_ospite
                    ap_totali = ap_casa + ap_ospite
                    ap_al_minuto = round(ap_totali / minuto_corrente, 2) if minuto_corrente > 0 else 0.0
                    
                    if tiri_totali > 0 or ap_totali > 0:
                        analisi_output = analizza_e_consiglia(nome_file_csv, squadra_casa, squadra_ospite, minuto=minuto_corrente, gol_totali=totale_gol_attuali, is_live=True)
                        nuovi_match_rilevanti.append({
                            "orario": f"{minuto_corrente}'", "partita": f"{squadra_casa} - {squadra_ospite}",
                            "punteggio": f"{gol_casa} - {gol_ospite}", "campionato": campionato_live,
                            "analisi": analisi_output
                        })
                        
                        # Parametri di attacco pericoloso attivi per invio Telegram
                        if (ap_al_minuto >= 1.15 and minuto_corrente >= 15 and tiri_totali >= 4) or (tiri_porta_totali >= 5):
                            messaggio = (
                                f"🔥 MILLENIUM ATTACCO IN CORSO 🔥\n\n"
                                f"Match: {squadra_casa} - {squadra_ospite}\n"
                                f"Minuto: {minuto_corrente}' | Score: {gol_casa}-{gol_ospite}\n\n"
                                f"Tiri in Porta: {tiri_porta_totali} (Totali: {tiri_totali})\n"
                                f"Pressione AP/Min: {ap_al_minuto}\n\n"
                                f"Analisi Storica:\n{analisi_output}"
                            )
                            invia_telegram(messaggio)
                            DASHBOARD_DATA["alert_inviati_totale"] += 1
                            time.sleep(2)
                            
            DASHBOARD_DATA["match_rilevanti"] = nuovi_match_rilevanti
            salva_dati_su_file()
    except Exception as e:
        print(f"Errore ciclo live: {e}", flush=True)

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
                        "campionato": campionato, "analisi": analizza_e_consiglia(nome_file_csv, squadra_casa, squadra_ospite, is_live=False)
                    })
            DASHBOARD_DATA["match_futuri"] = prossimi_match
            salva_dati_su_file()
    except Exception as e:
        print(f"Errore ciclo prematch: {e}", flush=True)

def invia_telegram(messaggio):
    if not TOKEN or not CHAT_ID:
        return
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": messaggio}, timeout=5)
    except Exception:
        pass

if __name__ == "__main__":
    # Avviamo il server Web in background per consentire l'ascolto della porta
    Thread(target=avvia_server, daemon=True).start()
    print("Millenium Bot Pronto e Attivo!", flush=True)
    
    while True:
        scansione_partite_live()
        scansione_prematch()
        time.sleep(60)
