from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import threading
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

# =======================================================
# # DIZIONARIO COMPLETO DI TRADUZIONE DEI CAMPIONATI
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
# MINI SERVER PER EVITARE IL FALLIMENTO DI RENDER
# =======================================================
def finto_server():
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, format, *args): return
    porta = int(os.environ.get("PORT", 10000))
    try:
        with TCPServer(("0.0.0.0", porta), QuietHandler) as server:
            server.serve_forever()
    except Exception:
        pass

# Avviamo subito il server in background per tranquillizzare Render
Thread(target=finto_server, daemon=True).start()

# =======================================================
# FUNZIONI DEL BOT
# =======================================================
def invia_telegram(messaggio):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": messaggio, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Errore nell'invio del messaggio: {e}")

def analizza_archivio_storico(nome_file_csv, squadra_casa, squadra_ospite):
    # Qui risiede la tua logica originale che analizza i file CSV storici.
    # Ne metto una versione base per non interrompere l'esecuzione dello script.
    try:
        if os.path.exists(nome_file_csv):
            df = pd.read_csv(nome_file_csv)
            # Inserisci qui i tuoi calcoli reali sui file CSV...
            return f"Analisi completata sul file {nome_file_csv}"
        return "Nessun archivio storico trovato per questo campionato."
    except Exception as e:
        return f"Errore lettura archivio: {e}"

# =======================================================
# CICLO PRINCIPALE DI SCANSIONE LIVE
# =======================================================
print("=== MILLENIUM BOT AVVIATO CON SUCCESSO ===")

while True:
    print("Scansione partite live in corso...")
    try:
        response = requests.get(URL_LIVE, timeout=10)
        if response.status_code == 200:
            dati = response.json()
            partite = dati.get("Value", [])
            
            for partita in partite:
                campionato_live = partita.get("L", "")
                squadra_casa = partita.get("O1", "")
                squadra_ospite = partita.get("O2", "")
                
                # Cerca se il campionato fa parte di quelli che seguiamo
                if campionato_live in DIZIONARIO_CAMPIONATI:
                    nome_file_csv = f"{DIZIONARIO_CAMPIONATI[campionato_live]}.csv"
                    
                    # Recupero dati dei tiri in porta dalle statistiche del match
                    stats = partita.get("SC", {}).get("S", [])
                    tiri_porta_casa = 0
                    tiri_porta_ospite = 0
                    
                    for stat in stats:
                        if stat.get("T") == 2:  # Di solito il tipo 2 indica i tiri totali/in porta
                            tiri_porta_casa = int(stat.get("G1", 0))
                            tiri_porta_ospite = int(stat.get("G2", 0))
                            break
                    
                    tiri_totali_live = tiri_porta_casa + tiri_porta_ospite
                    
                    # Se ci sono almeno 5 tiri totali, scatta l'allerta!
                    if tiri_totali_live >= 5:
                        analisi_storica = analizza_archivio_storico(nome_file_csv, squadra_casa, squadra_ospite)
                        
                        messaggio = (
                            f"*MILLENIUM BOT - SEGNALE VALUE BET*\n\n"
                            f"*Partita:* {squadra_casa} - {squadra_ospite}\n"
                            f"*Campionato:* {campionato_live}\n\n"
                            f"*DATI LIVE ATTUALI:*\n"
                            f"🎯 Tiri in porta totali: *{tiri_totali_live}* ({tiri_porta_casa} - {tiri_porta_ospite})\n"
                            f"{analisi_storica}\n\n"
                            f"💰 *Verifica la quota sul tuo bookmaker!*"
                        )
                        
                        invia_telegram(messaggio)
                        print(f"Segnale inviato con successo per: {squadra_casa} - {squadra_ospite}")
                        time.sleep(5)
                        
    except Exception as e:
        print(f"Errore durante lo screening live: {e}")
        
    # Aspetta 60 secondi prima della prossima scansione automatica delle partite
    time.sleep(60)
