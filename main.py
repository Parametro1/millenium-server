import time
import requests
import threading
from datetime import datetime
from flask import Flask

# ================= SERVER WEB PER TENERE SVEGLIO RENDER =================
app = Flask('')

@app.route('/')
def home():
    return "Millenium Bot è Online e in esecuzione!"

def run_web_server():
    # Render assegna automaticamente una porta, di default la 10000
    app.run(host='0.0.0.0', port=10000)

# ================= CONFIGURAZIONE BOT =================
TOKEN = "8561552292:AAFc2FArZKz4jzjM-NKDyFa7TS1bxNqIURE"
CHAT_ID = "6449164924"
API_KEY = "4fe9b78f88msh940cb3b6b194fb6p1e4c7djsn90d9709f1bf7"

CAMPIONATI_ESTIVI = {
    "USA": ["MLS", "USL Championship"],
    "Brazil": ["Serie A", "Serie B"],
    "Argentina": ["Liga Profesional"],
    "Sweden": ["Allsvenskan"],
    "Norway": ["Eliteserien"],
    "Finland": ["Veikkausliiga"],
    "Japan": ["J1 League"]
}

def invia_segnale_telegram(messaggio):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": messaggio, "parse_mode": "Markdown"}
    try:
        # NOTA: Su Render NON servono i proxies di PythonAnywhere! Connection diretta e pulita.
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ TELEGRAM: Segnale inviato con successo!")
        else:
            print(f"❌ TELEGRAM ERRORE: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ TELEGRAM ERRORE DI CONNETTIVITÀ: {e}")

def esegui_scansione():
    print(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] Avvio scansione dei match live...")
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    querystring = {"live": "all"}
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        if response.status_code != 200:
            return
        data = response.json()
        fixtures = data.get("response", [])
        match_trovati = 0
        
        for item in fixtures:
            league_info = item.get("league", {})
            country = league_info.get("country")
            league_name = league_info.get("name")
            
            if country in CAMPIONATI_ESTIVI and league_name in CAMPIONATI_ESTIVI[country]:
                fixture_info = item.get("fixture", {})
                status = fixture_info.get("status", {}).get("short")
                elapsed = fixture_info.get("status", {}).get("elapsed", 0)
                
                if status == "2H" or (status == "LIVE" and 45 <= elapsed <= 90):
                    goals = item.get("goals", {})
                    home_goals = goals.get("home", 0)
                    away_goals = goals.get("away", 0)
                    total_goals = home_goals + away_goals
                    
                    if home_goals == away_goals and total_goals <= 2:
                        teams = item.get("teams", {})
                        home_team = teams.get("home", {}).get("name")
                        away_team = teams.get("away", {}).get("name")
                        
                        msg = (
                            f"⚽ *MATCH WHITE LIST RILEVATO!* ⚽\n\n"
                            f"🏆 *Campionato:* {country} - {league_name}\n"
                            f"⚔️ *Partita:* {home_team} vs {away_team}\n"
                            f"⏱️ *Minuto:* {elapsed}'\n"
                            f"📊 *Risultato attuale:* {home_goals}-{away_goals}\n"
                            f"🔥 *Consiglio:* Valutare Over Live nei prossimi minuti!"
                        )
                        invia_segnale_telegram(msg)
                        match_trovati += 1
        if match_trovati == 0:
            print("🏟️ Scansione completata: Nessun match idoneo al momento.")
    except Exception as e:
        print(f"❌ Errore durante la scansione: {e}")

def ciclo_bot():
    print("🤖 MILLENIUM LIVE ENGINE SU RENDER ATTIVATO")
    invia_segnale_telegram("🔥 Il bot Millenium è ONLINE su Render.com! Pronto e indipendente dal PC.")
    while True:
        # Su Render lo lasciamo attivo h24 senza blocchi orari
        esegui_scansione()
        print("⏳ Prossimo controllo tra 8 minuti...")
        time.sleep(480)

if __name__ == "__main__":
    # Avvia il server web in un filo separato
    t = threading.Thread(target=run_web_server)
    t.daemon = True
    t.start()
    
    # Avvia il ciclo del bot scommesse
    ciclo_bot()
