from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import os
import time
import requests
import pandas as pd
from threading import Thread
import json
import calendar
from datetime import datetime

# --- CONFIGURAZIONI ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def invia_telegram(messaggio):
    # RIGA DI DEBUG: Se vedi questo nei log, sappiamo se le variabili sono caricate
    print(f"DEBUG: Token len={len(str(TOKEN)) if TOKEN else 0}, ChatID={CHAT_ID}", flush=True)
    
    if not TOKEN or not CHAT_ID: 
        print("Errore: Token o Chat ID mancanti!", flush=True)
        return
    try: 
        risposta = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": messaggio}, timeout=5)
        if risposta.status_code == 200:
            print("Messaggio inviato con successo!", flush=True)
        else:
            print(f"ERRORE TELEGRAM: {risposta.text}", flush=True)
    except Exception as e: 
        print(f"Errore connessione: {e}", flush=True)

def avvia_server():
    # Server minimo per mantenere il bot attivo su Render
    porta = int(os.environ.get("PORT", 10000))
    with TCPServer(("0.0.0.0", porta), SimpleHTTPRequestHandler) as server:
        server.serve_forever()

if __name__ == "__main__":
    Thread(target=avvia_server, daemon=True).start()
    print("Millenium Bot Pronto e Attivo!", flush=True)
    
    # Test di connessione
    invia_telegram("Test: Il bot è connesso e funzionante!")
    
    while True:
        print("Ciclo di scansione attivo...", flush=True)
        time.sleep(60)
