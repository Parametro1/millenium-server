import os
import time
from threading import Thread
import requests
import urllib3
from http.server import SimpleHTTPRequestHandler, HTTPServer

# Disabilita avvisi SSL per connessioni non verificate
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 1. VARIABILI D'AMBIENTE & CONFIGURAZIONE DIZIONARIO
# ==========================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "IL_TUO_TOKEN_DI_DEFAULT")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "IL_TUO_CHAT_ID_DI_DEFAULT")
PORT = int(os.getenv("PORT", 10000))

PARTITE_NOTIFICATE = set()

CAMPIONATI_DIZIONARIO = {
    "Calcio. Italia. Serie A": "I1",
    "Calcio. Inghilterra. Premier League": "E0",
    "Calcio. Spagna. Primera Division": "SP1",
    "Calcio. Germania. Bundesliga": "D1",
    "Calcio. Brasile. Campeonato Brasileiro Serie A": "BRA1",
    "Calcio. Argentina. Primera Division": "ARG1",
    "Calcio. Giappone. J-League": "JPN1",
    "Calcio. Svezia. Allsvenskan": "SWE1",
    "Calcio. Norvegia. Eliteserien": "NOR1",
    "Calcio. Finlandia. Veikkausliiga": "FIN1",
    "Calcio. Irlanda. Premier Division": "IRL1",
}

# ==========================================
# 2. FIX PORTA PER RENDER (SENZA FLASK)
# ==========================================
def avvia_server_finto():
    """Apre la porta richiesta da Render usando i moduli nativi di Python"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), SimpleHTTPRequestHandler)
        server.serve_forever()
    except Exception:
        pass

# ==========================================
# 3. INVIO SEGNALI TELEGRAM
# ==========================================
def invia_telegram(messaggio):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": messaggio,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=10)
        print("[TELEGRAM] Segnale inviato con successo!")
    except Exception as e:
        print(f"[TELEGRAM ERRORE] Impossibile inviare messaggio: {e}")

# ==========================================
# 4. MOTORE DI ANALISI STORICA (.CSV)
# ==========================================
def calcola_media_csv(file_csv, squadra_casa, squadra_trasferta):
    path_file = f"database/{file_csv}.csv"
    if not os.path.exists(path_file):
        return 0.0, 0.0, 0.0
    
    # Logica mock originale
    media_casa = 1.35
    media_trasferta = 1.20
    media_combinata = media_casa + media_trasferta
    return media_combinata, media_casa, media_trasferta

# ==========================================
# 5. ALGORITMO DI ATTIVAZIONE ED ELABORAZIONE LIVE
# ==========================================
def analizza_partita(match_data):
    try:
        nome_campionato = match_data.get("campionato")
        if nome_campionato not in CAMPIONATI_DIZIONARIO:
            return
        
        file_csv = CAMPIONATI_DIZIONARIO[nome_campionato]
        squadra_casa = match_data.get("casa")
        squadra_trasferta = match_data.get("trasferta")
        match_id = match_data.get("id")
        
        if match_id in PARTITE_NOTIFICATE:
            return

        minuto = match_data.get("minuto", 0)
        gol_casa = match_data.get("gol_casa", 0)
        gol_trasferta = match_data.get("gol_trasferta", 0)
        
        ap = match_data.get("attacchi_pericolosi", 0)
        tiri_porta = match_data.get("tiri_in_porta", 0)
        tiri_totali = match_data.get("tiri_totali", 0)
        corner = match_data.get("corner", 0)
        
        # Calcolo AP/Minuto
        ap_minuto = round(ap / minuto, 2) if minuto > 0 else 0
        
        # 🎯 SOGLIE AGGIORNATE CON ALLINEAMENTO PERFETTO
        trigger_a = (ap_minuto >= 0.50 and minuto >= 10 and tiri_totali >= 3 and corner >= 2)
        trigger_b = (tiri_porta >= 5 and corner >= 2)
        
        if trigger_a or trigger_b:
            media_totale, med_c, med_t = calcola_media_csv(file_csv, squadra_casa, squadra_trasferta)
            
            if media_totale < 2.40:
                print(f"[FILTRO] {squadra_casa} - {squadra_trasferta} scartata per Media Storica insufficiente ({media_totale})")
                return
            
            if 0 <= minuto <= 35:
                consiglio = "OVER 0.5 HT"
            elif 36 <= minuto <= 65:
                consiglio = "OVER LIVE"
            elif 66 <= minuto <= 82:
                consiglio = "OVER 0.5 FINALE"
            else:
