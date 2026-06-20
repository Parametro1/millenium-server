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
URL_LIVE = "https://1xbet.com/LiveFeed/GetMatchesVzip?sports=1&count=50&lng=it"
URL_FUTURE = "https://1xbet.com/LineFeed/GetMatchesVzip?sports=1&count=50&lng=it"
DATA_FILE = "dashboard_data.json"

# --- FUNZIONI DI SERVIZIO ---
def invia_telegram(messaggio):
    if not TOKEN or not CHAT_ID: 
        print("Errore: Token o Chat ID mancanti!", flush=True)
        return
    try: 
        risposta = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": messaggio}, timeout=5)
        if risposta.status_code != 200:
            print(f"ERRORE TELEGRAM: {risposta.text}", flush=True)
        else:
            print("Messaggio inviato con successo!", flush=True)
    except Exception as e: 
        print(f"Errore connessione: {e}", flush=True)

def avvia_server():
    porta = int(os.environ.get("PORT", 10000))
    with TCPServer(("0.0.0.0", porta), SimpleHTTPRequestHandler) as server:
        server.serve_forever()

def scansione_partite_live():
    print("Ciclo di scansione attivo...", flush=True)
    # Qui inserisci il resto della tua logica di scansione (non l'ho incollata per brevità)

def scansione_prematch():
    # Qui inserisci il resto della tua logica prematch
    pass

# --- AVVIO BOT ---
if __name__ == "__main__":
    Thread(target=avvia_server, daemon=True).start()
    print("Millenium Bot Pronto e Attivo!", flush=True)
    
    invia_telegram("Test: Il bot è connesso e funzionante!")
    
    while True:
        scansione_partite_live()
        scansione_prematch()
        time.sleep(60)
