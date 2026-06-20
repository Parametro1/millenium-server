import os
import time
import requests
import pandas as pd
from threading import Thread
import json
import calendar
from datetime import datetime
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

# --- CONFIGURAZIONI ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
URL_LIVE = "https://1xbet.com/LiveFeed/GetMatchesVzip?sports=1&count=50&lng=it"
URL_FUTURE = "https://1xbet.com/LineFeed/GetMatchesVzip?sports=1&count=50&lng=it"
DATA_FILE = "dashboard_data.json"

# --- FUNZIONI DI SUPPORTO (Ordine Corretto) ---

def invia_telegram(messaggio):
    if not TOKEN or not CHAT_ID: return
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": messaggio}, timeout=5)
    except Exception as e:
        print(f"Errore Telegram: {e}", flush=True)

def salva_dati_su_file(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Errore JSON: {e}", flush=True)

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
            output += f"<span style='color:#10b981;font-weight:bold;'>{consiglio_gol}{consiglio_corner}</span>" if consiglio_gol != "No Bet" else "No Bet"
        else: output += "STUDIO: Analisi pronta."
        return output
    except: return "Errore calcolo."

# --- LOGICHE PRINCIPALI E CICLI (In fondo al file) ---
# [Qui dovresti incollare il resto della tua logica di scansione]
