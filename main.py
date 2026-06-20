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
def avvia_server():
    # Questa funzione fa partire il server web sulla porta richiesta da Render
    from http.server import SimpleHTTPRequestHandler
    from socketserver import TCPServer
    import os
    
    class MyHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Millenium Bot PRO Online</h1></body></html>")

    porta = int(os.environ.get("PORT", 10000))
    try:
        with TCPServer(("", porta), MyHandler) as httpd:
            print(f"Server web attivo sulla porta {porta}", flush=True)
            httpd.serve_forever()
    except Exception as e:
        print(f"Errore nell'avvio del server: {e}", flush=True)

# --- LOGICA PRINCIPALE ---
if __name__ == "__main__":
    # 1. Avviamo il server web reale
    print("Accensione del server web...", flush=True)
    Thread(target=avvia_server, daemon=True).start()
    
    # 2. Aspettiamo 5 secondi per far agganciare la porta a Render
    time.sleep(5) 
    
    print("Millenium Bot Pronto e Attivo!", flush=True)
    invia_telegram("✅ Motore Millenium stabilizzato e Web Server ATTIVO!")
    
    # 3. Ciclo infinito delle scansioni
    while True:
        scansione_partite_live()
        scansione_prematch()
        time.sleep(60)
