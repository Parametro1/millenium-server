import os
import time
import requests
import pandas as pd

# =====================================================================
# CONFIGURAZIONI PRINCIPALI (Prese da Render)
# =====================================================================
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
URL_LIVE = "https://1xbet.com/LiveFeed/GetMatchesVZip?sports=1&count=50&lng=it"

# =====================================================================
# DIZIONARIO COMPLETO DI TRADUZIONE DEI CAMPIONATI
# =====================================================================
DIZIONARIO_CAMPIONATI = {
    "Calcio. Italia. Serie A": "I1",
    "Calcio. Italia. Serie B": "I2",
    "Calcio. Inghilterra. Premier League": "E0",
    "Calcio. Inghilterra. Championship": "E1",
    "Calcio. Spagna. Primera Division": "SP1",
    "Calcio. Spagna. Segunda Division": "SP2",
    "Calcio. Germania. Bundesliga": "D1",
    "Calcio. Germania. 2. Bundesliga": "D2",
    "Calcio. Francia. Ligue 1": "F1",
    "Calcio. Francia. Ligue 2": "F2",
    "Calcio. Olanda. Eredivisie": "N1",
    "Calcio. Svezia. Superettan": "SWE2",
    "Calcio. Svezia. Allsvenskan": "SWE1",
    "Calcio. Turchia. SuperLig": "T1",
    "Calcio. USA. MLS": "USA",
    "Calcio. Argentina. Primera Division": "ARG",
    "Calcio. Austria. Bundesliga": "AUT",
    "Calcio. Brasile. Serie A": "BRA",
    "Calcio. Cina. Super League": "CHN",
    "Calcio. Danimarca. Superligaen": "DNK",
    "Calcio. Finlandia. Veikkausliiga": "FIN",
    "Calcio. Irlanda. Premier Division": "IRL",
    "Calcio. Giappone. J1 League": "JPN",
    "Calcio. Messico. Liga MX": "MEX",
    "Calcio. Norvegia. Eliteserien": "NOR",
    "Calcio. Polonia. Ekstraklasa": "POL",
    "Calcio. Romania. Liga I": "ROU",
    "Calcio. Russia. Premier League": "RUS"
}

def invia_telegram(messaggio):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": messaggio, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Errore invio Telegram: {e}")

def analizza_archivio_storico(nome_file_base, casa_live, ospite_live):
    file_standard = f"{nome_file_base}.csv"
    file_maiuscolo = f"{nome_file_base}.CSV"
    nome_file = file_standard if os.path.exists(file_standard) else file_maiuscolo
    
    if not os.path.exists(nome_file):
        return f"⚠️ File database `{nome_file_base}` non trovato su GitHub."
        
    try:
        df = pd.read_csv(nome_file)
        casa_clean = casa_live.split()[0].lower() if casa_live else ""
        ospite_clean = ospite_live.split()[0].lower() if ospite_live else ""
        
        df['Home_Clean'] = df['HomeTeam'].astype(str).str.lower()
        df['Away_Clean'] = df['AwayTeam'].astype(str).str.lower()
        
        match_casa = df[df['Home_Clean'].str.contains(casa_clean, na=False)]
        match_ospite = df[df['Away_Clean'].str.contains(ospite_clean, na=False)]
        
        totale_match = len(match_casa) + len(match_ospite)
        if totale_match == 0:
            return "📊 *Dati storici:* Squadre non trovate con l'algoritmo parziale."
            
        over25_casa = len(match_casa[(match_casa['FTHG'] + match_casa['FTAG']) > 2])
        over25_ospite = len(match_ospite[(match_ospite['FTHG'] + match_ospite['FTAG']) > 2])
        perc_over25 = ((over25_casa + over25_ospite) / totale_match) * 100
        
        over05_ht_casa = len(match_casa[(match_casa['HTHG'] + match_casa['HTAG']) > 0])
        over05_ht_ospite = len(match_ospite[(match_ospite['HTHG'] + match_ospite['HTAG']) > 0])
        perc_over05_ht = ((over05_ht_casa + over05_ht_ospite) / totale_match) * 100
        
        return (
            f"📊 *ANALISI FOOTBALL-DATA ({totale_match} match storici):*\n"
            f"🔥 Storico Over 2.5 Finale: *{round(perc_over25, 1)}%*\n"
            f"⏱️ Storico Over 0.5 1° Tempo: *{round(perc_over05_ht, 1)}%*"
        )
    except Exception as e:
        return f"❌ Errore lettura dati storici: {e}"

def scansione_partite():
    print("Scansione palinsesto live in corso...")
    try:
        response = requests.get(URL_LIVE).json()
        partite = response.get("Value", [])
        
        for partita in partite:
            campionato_live = partita.get("League", "")
            if campionato_live in DIZIONARIO_CAMPIONATI:
                nome_file_csv = DIZIONARIO_CAMPIONATI[campionato_live]
                squadra_casa = partita.get("Opp1", "")
                squadra_ospite = partita.get("Opp2", "")
                
                tiri_porta_casa = 0
                tiri_porta_ospite = 0
                stats = partita.get("Stat", {}).get("Period", [])
                if stats:
                    for s in stats:
                        if s.get("Type") == "ShotsOnTarget":
                            tiri_porta_casa = int(s.get("Sub1", 0))
                            tiri_porta_ospite = int(s.get("Sub2", 0))
                
                tiri_totali_live = tiri_porta_casa + tiri_porta_ospite
                if tiri_totali_live >= 5:
                    analisi_storica = analizza_archivio_storico(nome_file_csv, squadra_casa, squadra_ospite)
                    messaggio = (
                        f"🤖 *MILLENIUM BOT - SEGNALE VALUE BET*\n"
                        f"🏟️ *Partita:* {squadra_casa} - {squadra_ospite}\n"
                        f"🏆 *Campionato:* {campionato_live}\n\n"
                        f"⚡ *DATI LIVE ATTUALI:*\n"
                        f"🎯 Tiri in porta totali: *{tiri_totali_live}* ({tiri_porta_casa} - {tiri_porta_ospite})\n\n"
                        f"{analisi_storica}\n\n"
                        f"💰 *Verifica la quota sul tuo bookmaker!*"
                    )
                    invia_telegram(messaggio)
                    print(f"Segnale inviato con successo per: {squadra_casa} - {squadra_ospite}")
                    time.sleep(5)
                    
    except Exception as e:
        print(f"Errore durante lo screening live: {e}")

if __name__ == "__main__":
    print("Millenium Bot avviato e pronto a calcolare!")
    while True:
        scansione_partite()
        time.sleep(60)
