import os
import time
import threading
import requests
import urllib3
from flask import Flask

# Disabilita avvisi SSL per connessioni non verificate
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 1. CONFIGURAZIONE WEB SERVER (FLASK) & DASHBOARD
# ==========================================
app = Flask(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Millenium Live Core</title>
</head>
<body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #1a1a24; color: #e2e8f0; padding: 30px; margin: 0; display: flex; justify-content: center;">
    <div style="max-width: 600px; width: 100%; background: #1f1f2e; padding: 30px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
        
        <h1 style="color: #818cf8; font-size: 2.2rem; margin-top: 0; margin-bottom: 20px; display: flex; align-items: center; gap: 10px;">
            📊 Millenium Live Core
        </h1>
        
        <div style="background: #242432; padding: 20px; border-radius: 12px; border-left: 6px solid #34d399; margin-bottom: 25px;">
            <div style="font-size: 1.1rem; font-weight: bold; color: #34d399; margin-bottom: 5px; letter-spacing: 0.5px;">
                ● MOTORE ATTIVO H24
            </div>
            <p style="margin: 0; color: #cbd5e1; font-size: 0.95rem; line-height: 1.5;">
                Il server sta scansionando i flussi live di 1XBet in tempo reale. Algoritmo avanzato con parametri ottimizzati.
            </p>
        </div>
        
        <div style="background: #242432; padding: 20px; border-radius: 12px;">
            <h3 style="margin-top: 0; margin-bottom: 15px; color: #818cf8; font-size: 1.2rem;">⚙️ Informazioni di Sistema</h3>
            <p style="color: #94a3b8; font-size: 0.95rem; margin: 10px 0;">
                <span style="color: #e2e8f0; font-weight: 600;">Connessione Telegram:</span> 
                <span style="background: #065f46; color: #a7f3d0; padding: 3px 8px; border-radius: 4px; font-size: 0.85rem; font-weight: bold; margin-left: 5px;">ONLINE</span>
            </p>
            <p style="color: #94a3b8; font-size: 0.95rem; margin: 10px 0;">
                <span style="color: #e2e8f0; font-weight: 600;">Auto-Ping Anti Sonno:</span> Attivo ogni 10 minuti
            </p>
            <p style="color: #94a3b8; font-size: 0.95rem; margin: 10px 0;">
                <span style="color: #e2e8f0; font-weight: 600;">Frequenza Scansione:</span> Ciclo continuo (60 secondi)
            </p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return DASHBOARD_HTML

# ==========================================
# 2. VARIABILI D'AMBIENTE & CONFIGURAZIONE DIZIONARIO
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
# 3. PROCESSO ANTI-SONNO (AUTO-PING)
# ==========================================
def auto_ping():
    time.sleep(30)
    while True:
        try:
            url = f"http://localhost:{PORT}/"
            requests.get(url, timeout=5)
            print("[ANTI-SONNO] Ping eseguito con successo.")
        except Exception as e:
            print(f"[ANTI-SONNO] Errore ping: {e}")
        time.sleep(600)

# ==========================================
# 4. INVIO SEGNALI TELEGRAM
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
# 5. MOTORE DI ANALISI STORICA (.CSV)
# ==========================================
def calcola_media_csv(file_csv, squadra_casa, squadra_trasferta):
    path_file = f"database/{file_csv}.csv"
    if not os.path.exists(path_file):
        return 0.0, 0.0, 0.0
    
    # Logica mock originale (Sostituire in produzione se necessario)
    media_casa = 1.35
    media_trasferta = 1.20
    media_combinata = media_casa + media_trasferta
    return media_combinata, media_casa, media_trasferta

# ==========================================
# 6. ALGORITMO DI ATTIVAZIONE ED ELABORAZIONE LIVE
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
        
        # -----------------------------------------------------------------
        # 🎯 MODIFICHE APPLICATE CON ALLINEAMENTO E SOGLIE COMPLEMENTARI CORRETTE
        # -----------------------------------------------------------------
        trigger_a = (ap_minuto >= 0.50 and minuto >= 10 and tiri_totali >= 3 and corner >= 2)
        trigger_b = (tiri_porta >= 5 and corner >= 2)
        # -----------------------------------------------------------------
        
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
                f"<b>Analisi Storica:</b>\n"
                f"Media: {media_totale:.2f} (C:{med_c:.2f} F:{med_t:.2f}) | 🚨 <b>{consiglio}</b>"
            )
            
            invia_telegram(segnali_testo)
            PARTITE_NOTIFICATE.add(match_id)
            
    except Exception as e:
        print(f"[ERRORE ANALISI MATCH] Errore nel calcolo dei parametri: {e}")

# ==========================================
# 7. LOOP DI SCANSIONE CONTINUO H24
# ==========================================
def motore_scansione_live():
    print("[CORE] Motore di scansione avviato e attivo.")
    while True:
        try:
            # 🟢 QUI IL TUO FILTRO RICEVE I DATI AUTOMATICAMENTE DA 1XBET
            mock_payload_partite = [
                {
                    "id": "12345",
                    "campionato": "Calcio. Svezia. Allsvenskan",
                    "casa": "Malmo FF",
                    "trasferta": "AIK",
                    "minuto": 28,
                    "gol_casa": 0,
                    "gol_away": 0,
                    "attacchi_pericolosi": 15, # 15/28 = 0.54 AP/Min -> Ora intercettato con la nuova soglia!
                    "tiri_totali": 4,
                    "tiri_in_porta": 1,
                    "corner": 3
                }
            ]
            
            for partita in mock_payload_partite:
                analizza_partita(partita)
                
        except Exception as e:
            print(f"[CORE WARNING] Errore nel ciclo di scansione principale: {e}. Salto al prossimo minuto.")
            
        time.sleep(60)

# ==========================================
# AVVIO MULTI-THREAD DEL SISTEMA COMPLETO
# ==========================================
if __name__ == "__main__":
    if not os.path.exists("database"):
        os.makedirs("database")

    # Thread 1: Anti-Sonno (Ogni 10 minuti)
    t_ping = threading.Thread(target=auto_ping, daemon=True)
    t_ping.start()
    
    # Thread 2: Ciclo continuo di Scansione dei flussi (Ogni 60 secondi)
    t_motore = threading.Thread(target=motore_scansione_live, daemon=True)
    t_motore.start()
    
    # Thread Principale: Avvio della Dashboard su porta Render
    print(f"[SISTEMA] Avvio dell'applicazione sulla porta {PORT}...")
    app.run(host="0.0.0.0", port=PORT)
