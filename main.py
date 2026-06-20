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

# --- FUNZIONE TELEGRAM CORRETTA ---
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
        print(f"Errore connessione Telegram: {e}", flush=True)

# --- FUNZIONI ORIGINALI (Le tue) ---
# (Qui il bot continuerà a usare le tue funzioni di analisi, scansione e server che avevi prima)
# Assicurati di aver incollato qui sotto tutte le tue funzioni originali fino a 'if __name__ == "__main__":'

if __name__ == "__main__":
    Thread(target=avvia_server, daemon=True).start()
    print("Millenium Bot Pronto e Attivo!", flush=True)
    
    # RIGA DI TEST
    invia_telegram("Test: Il bot è connesso e funzionante!")
    
    while True:
        scansione_partite_live()
        scansione_prematch()
        time.sleep(60)
