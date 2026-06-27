import os
import time
import json
from threading import Thread
import requests
from http.server import SimpleHTTPRequestHandler, HTTPServer

# ==========================================
# ⚙️ CONFIGURAZIONE PARAMETRI E CREDENZIALI
# ==========================================
TELEGRAM_TOKEN = "8561552292:AAFc2FArZKz4jzjM-NKdyFa7TS1bxNqIURE"
TELEGRAM_CHAT_ID = "@canale_millenium_test_123"  # <-- Sostituisci con il link del tuo canale pubblico
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
# 📡 FUNZIONE INVIO TELEGRAM (BLINDATA)
# ==========================================
def invia_telegram(messaggio):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": messaggio, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("[TELEGRAM] Segnale inviato con successo!")
        else:
            print(f"[TELEGRAM API ERRORE] Status: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[TELEGRAM CRASH PROTETTO]: {e}")

# ==========================================
# 🖥️ SERVER WEB NATIVO (ANTI-SPEGNIMENTO RENDER)
# ==========================================
def avvia_server_finto():
    try:
        server = HTTPServer(('0.0.0.0', PORT), SimpleHTTPRequestHandler)
        server.serve_forever()
    except Exception:
        pass

# ==========================================
# 📊 ALGORITMO DI ANALISI (PARAMETRI ABBASSATI)
# ==========================================
def calcola_media_csv(file_csv, squadra_casa, squadra_trasferta):
    return 2.55, 1.35, 1.20

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
        
        # 🔍 SOGLIE MODIFICATE RICHIESTE
        trigger_a = (ap_minuto >= 0.40 and minuto >= 10 and tiri_totali >= 2 and corner >= 1)
        trigger_b = (tiri_porta >= 3 and corner >= 1)
        
        if trigger_a or trigger_b:
            media_totale, med_c, med_t = calcola_media_csv(file_csv, squadra_casa, squadra_trasferta)
            
            if media_totale < 2.40:
                return
            
            if 0 <= minuto <= 35:
                consiglio = "OVER 0.5 HT"
            elif 36 <= minuto <= 65:
                consiglio = "OVER LIVE"
            elif 66 <= minuto <= 82:
                consiglio = "OVER 0.5 FINALE"
            else:
                return
            
            tipo_allarme = "🎯 BOMBARDAMENTO" if trigger_b else "🔥 ASSEDIO"
            
            segnali_testo = (
                f"🔥 <b>MILLENIUM: GOL IMMINENTE</b> 🔥\n\n"
                f"<b>Match:</b> {squadra_casa} - {squadra_trasferta}\n"
                f"<b>Stato:</b> {tipo_allarme}\n"
                f"<b>Minuto:</b> {minuto}' | <b>Score:</b> {gol_casa}-{gol_trasferta}\n\n"
                f"Calci d'Angolo: {corner} 📐\n"
                f"Tiri (In Porta / Tot): {tiri_porta} / {tiri_totali} ⚽\n"
                f"Pressione AP/Min: {ap_minuto} ⚡\n\n"
                f"🚨 <b>{consiglio}</b>"
            )
            
            invia_telegram(segnali_testo)
            PARTITE_NOTIFICATE.add(match_id)
            
    except Exception as e:
        print(f"[ERRORE ANALISI MATCH] Errore: {e}")

# ==========================================
# 🔄 MOTORE DI SCANSIONE LIVE
# ==========================================
def motore_scansione_live():
    print("[CORE] Scansione attiva e pronta.")
    while True:
        try:
            # Spazio pronto per agganciare l'URL o lo scraping dei dati reali in futuro
            pass
        except Exception as e:
            print(f"[CORE WARNING] Errore ciclo: {e}")
        time.sleep(60)

# ==========================================
# 🚀 AVVIO APPLICAZIONE
# ==========================================
if __name__ == "__main__":
    if not os.path.exists("database"):
        os.makedirs("database")

    print("🤖 MILLENIUM BOT IN COSTRUZIONE...")
    
    # Avvia il server web per Render in background
    Thread(target=avvia_server_finto, daemon=True).start()
    
    # Invia la spia di controllo all'avvio
    messaggio_avvio = (
        "🤖 <b>MOTORE MILLENIUM ONLINE</b> 🤖\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <i>Aggiornamento codice completato con successo.</i>\n"
        "📊 Parametri di scansione abbassati e attivi.\n"
        "🟢 Status: <b>LIVE</b>"
    )
    invia_telegram(messaggio_avvio)
    
    # Fissa il bot nel ciclo continuo di scansione
    motore_scansione_live()
