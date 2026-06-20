import os
import time
import requests
import pandas as pd
import json
from threading import Thread
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

# --- CONFIGURAZIONI ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PORT = int(os.getenv("PORT", 10000))

# --- FUNZIONI DI SUPPORTO ---
def invia_telegram(messaggio):
    if not TOKEN or not CHAT_ID: return
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": messaggio}, timeout=5)
    except Exception as e:
        print(f"Errore Telegram: {e}", flush=True)

def analizza_e_consiglia(nome_file_csv, casa_live, ospite_live, minuto=None, gol_totali=0, is_live=False):
    file_standard = f"{nome_file_csv}.csv"
    file_maiuscolo = f"{nome_file_csv}.CSV"
    nome_file = file_standard if os.path.exists(file_standard) else file_maiuscolo
    if not os.path.exists(nome_file): return "Nessun CSV trovato."
    try:
        df = pd.read_csv(nome_file)
        partite_casa = df[df['HomeTeam'].str.contains(casa_live, case=False, na=False)]
        partite_ospite = df[df['AwayTeam'].str.contains(ospite_live, case=False, na=False)]
        media_gol = (partite_casa['FTHG'].mean() if not partite_casa.empty else 0.0) + (partite_ospite['FTAG'].mean() if not partite_ospite.empty else 0.0)
        media_corner = (partite_casa['HC'].mean() if not partite_casa.empty and 'HC' in df.columns else 0.0) + (partite_ospite['AC'].mean() if not partite_ospite.empty and 'AC' in df.columns else 0.0)
        
        output = f"Gol: {media_gol:.2f} | Corner: {media_corner:.1f} | "
        if is_live and minuto is not None:
            consiglio_gol = "No Bet"
            if media_gol >= 2.40:
                if minuto <= 35: consiglio_gol = "OVER 0.5 HT"
                elif minuto <= 65: consiglio_gol = f"OVER {gol_totali + 1.5} LIVE"
                elif minuto <= 82: consiglio_gol = f"OVER {gol_totali + 0.5} FINALE"
            consiglio_corner = " + OVER CORNER" if media_corner >= 9.5 else ""
            output += f"{consiglio_gol}{consiglio_corner}" if consiglio_gol != "No Bet" else "No Bet"
        else: output += "Analisi pronta."
        return output
    except: return "Errore calcolo."

# --- WEB SERVER PER RENDER ---
def run_server():
    with TCPServer(("", PORT), SimpleHTTPRequestHandler) as httpd:
        print(f"Server attivo sulla porta {PORT}")
        httpd.serve_forever()

# --- LOGICA PRINCIPALE ---
if __name__ == "__main__":
    # Avvia il server web in un thread separato
    server_thread = Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    print("Millenium Bot PRO avviato con successo!")
    
    # Qui il tuo bot continua a girare
    while True:
        # Inserisci qui la logica di scansione (quella che avevi prima)
        time.sleep(60)
