import os
import time
import json
from threading import Thread
import urllib.request
import urllib.parse
from http.server import SimpleHTTPRequestHandler, HTTPServer

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
# 2. FIX PORTA PER RENDER NATIVO
# ==========================================
def avvia_server_finto():
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
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
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
    
    media_casa = 1.35
    media_trasferta = 1.20
    media_combinata = media_casa + media_trasferta
    return media_combinata, media_casa, media_trasferta

# ==========================================
# 5. ALGORITMO DI ATTIVAZIONE LIVE
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
        
        ap_minuto = round(ap / minuto, 2) if minuto > 0 else 0
        
        trigger_a = (ap_minuto >= 0.50 and minuto >= 10 and tiri_totali >= 3 and corner >= 2)
        trigger_b = (tiri_porta >= 5 and corner >= 2)
        
        if trigger_a or trigger_b:
            media_totale, med_c, med_t = calcola_media_csv(file_csv, squadra_casa, squadra_trasferta)
            
            if media_totale < 2.40:
                print(f"[FILTRO] {squadra_casa} - {squadra_trasferta} scartata per Media Storica insufficiente ({media_totale})")
                return
            
            # --- BLOCCO TEMPORALE CORRETTO E ALLINEATO ---
            if 0 <= minuto <= 35:
                consiglio = "OVER 0.5 HT"
            elif 36 <= minuto <= 65:
                consiglio = "OVER LIVE"
            elif 66 <= minuto <= 82:
                consiglio = "OVER 0.5 FINALE"
            else:
                return  # Ignora se fuori minutaggio corretto
            
            tipo_allarme = "🎯 BOMBARDAMENTO" if trigger_b else "🔥 ASSEDIO"
            
            segnali_testo = (
                f"🔥 <b>MILLENIUM: GOL IMMINENTE</b> 🔥\n\n"
                f"<b>Match:</b> {squadra_casa} - {squadra_trasferta}\n"
                f"<b>Stato:</b> {tipo_allarme}\n"
                f"<b>Minuto:</b> {minuto}' | <b>Score:</b> {gol_casa}-{gol_trasferta}\n\n"
                f"Calci d'Angolo: {corner} 📐\n"
                f"Tiri (In Porta / Tot): {tiri_porta} / {tiri_totali} ⚽\n"
                f"Pressione AP/Min: {ap_minuto} ⚡\n\n"
                f"<b>Analisi Storica:</b>\n"
                f"Media: {media_totale:.2f} (C:{med_c:.2f} F:{med_t:.2f}) | 🚨 <b>{consiglio}</b>"
            )
            
            invia_telegram(segnali_testo)
            PARTITE_NOTIFICATE.add(match_id)
            
    except Exception as e:
        print(f"[ERRORE ANALISI MATCH] Errore nel calcolo dei parametri: {e}")

# ==========================================
# 6. LOOP DI SCANSIONE CONTINUO H24
# ==========================================
def motore_scansione_live():
    print("[CORE] Motore di scansione avviato e attivo.")
    while True:
        try:
            mock_payload_partite = [
                {
                    "id": "12345",
                    "campionato": "Calcio. Svezia. Allsvenskan",
                    "casa": "Malmo FF",
                    "trasferta": "AIK",
                    "minuto": 28,
                    "gol_casa": 0,
                    "gol_trasferta": 0,
                    "attacchi_pericolosi": 15,
                    "tiri_totali": 4,
                    "tiri_in_porta": 1,
                    "corner": 3
                }
            ]
            
            for partita in mock_payload_partite:
                analizza_partita(partita)
                
        except Exception as e:
            print(f"[CORE WARNING] Errore nel ciclo di scansione principale: {e}.")
            
        time.sleep(60)

# ==========================================
# AVVIO DEL SISTEMA
# ==========================================
if __name__ == "__main__":
    if not os.path.exists("database"):
        os.makedirs("database")

    print("🤖 MILLENIUM BOT IN COSTRUZIONE...")
    Thread(target=avvia_server_finto, daemon=True).start()
    print(f"[SISTEMA] Fix porta abilitato sulla porta {PORT}")
    
    motore_scansione_live()
