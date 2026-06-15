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

# =======================================================
# FUNZIONI DEL BOT
# =======================================================
def invia_telegram(messaggio):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": messaggio, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Errore invio Telegram: {e}")

def analizza_archivio_storico(nome_file_base, casa_live, ospite_live):
    # La tua logica originale identica alle foto (Righe 68-71)
    file_standard = f"{nome_file_base}.csv"
    file_maiuscolo = f"{nome_file_base}.CSV"
    nome_file = file_standard if os.path.exists(file_standard) else file_maiuscolo
    
    try:
        if os.path.exists(nome_file):
            df = pd.read_csv(nome_file)
            
            # Filtriamo i match storici delle due squadre nel file CSV
            partite_casa = df[df['HomeTeam'].str.contains(casa_live, case=False, na=False)]
            partite_ospite = df[df['AwayTeam'].str.contains(ospite_live, case=False, na=False)]
            
            output = f"📊 *Analisi Archivio ({nome_file}):*\n"
            
            # Calcolo media gol fatti in casa
            if not partite_casa.empty and 'FTHG' in df.columns:
                media_fatti_casa = partite_casa['FTHG'].mean()
                output += f"🏠 {casa_live} (In Casa) Media Gol Fatti: *{media_fatti_casa:.2f}*\n"
            else:
                output += f"🏠 Dati storici in casa per {casa_live} insufficienti.\n"
                
            # Calcolo media gol fatti in trasferta
            if not partite_ospite.empty and 'FTAG' in df.columns:
                media_fatti_ospite = partite_ospite['FTAG'].mean()
                output += f"🚀 {ospite_live} (Fuori Casa) Media Gol Fatti: *{media_fatti_ospite:.2f}*"
            else:
                output += f"🚀 Dati storici fuori casa per {ospite_live} insufficienti."
                
            return output
        else:
            return f"⚠️ *Analisi Archivio:* File {nome_file} non trovato sul server."
    except Exception as e:
        return f"⚠️ *Errore calcolo archivio:* {str(e)}"

# =======================================================
# FUNZIONE PRINCIPALE DI SCANSIONE LIVE
# =======================================================
def scansione_partite():
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
                
                if campionato_live in DIZIONARIO_CAMPIONATI:
                    nome_file_base = DIZIONARIO_CAMPIONATI[campionato_live]
                    
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
                    
                    # Se ci sono almeno 5 tiri totali, scatta l'allerta con l'analisi!
                    if tiri_totali_live >= 5:
                        analisi_storica = analizza_archivio_storico(nome_file_base, squadra_casa, squadra_ospite)
                        
                        messaggio = (
                            f"*MILLENIUM BOT - SEGNALE VALUE BET*\n\n"
                            f"*Partita:* {squadra_casa} - {squadra_ospite}\n"
                            f"*Campionato:* {campionato_live}\n\n"
                            f"*DATI LIVE ATTUALI:*\n"
                            f"🎯 Tiri in porta totali: *{tiri_totali_live}* ({tiri_porta_casa} - {tiri_porta_ospite})\n\n"
                            f"{analisi_storica}\n\n"
                            f"💰 *Verifica la quota sul tuo bookmaker!*"
                        )
                        
                        invia_telegram(messaggio)
                        print(f"Segnale inviato su Telegram per: {squadra_casa} - {squadra_ospite}")
                        time.sleep(5)
                        
    except Exception as e:
        print(f"Errore durante lo screening live: {e}")

# =======================================================
# BLOCCO DI AVVIO REALE DEL PROCESSO
# =======================================================
if __name__ == "__main__":
    # Avvia il finto server web in un thread separato per Render
    Thread(target=finto_server, daemon=True).start()
    
    print("Millenium Bot avviato e pronto a calcolare!")
    
    while True:
        scansione_partite()
        time.sleep(60)
