import os
import time
import requests
import pandas as pd
from difflib import get_close_matches

# =====================================================================
# ⚙️ CONFIGURAZIONE PARAMETRI & TOKEN
# =====================================================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "IL_TUO_TOKEN_BOT")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "IL_TUO_ID_CANALE")

# Collegamento automatico Campionato -> File Archivio CSV
DIZIONARIO_CAMPIONATI = {
    "Inghilterra Championship": "E1.CSV",
    "Australia A-League": "ast_pulito.csv"
}

# =====================================================================
# 🧠 FUNZIONE ANALISI E SUPERAMENTO DILEMMA NOMI
# =====================================================================
def analizza_e_consiglia(file_csv, casa_live, trasferta_live, minuto):
    """
    Legge lo storico, adatta i nomi delle squadre live a quelli del CSV
    e restituisce un consiglio basato sulle medie gol.
    """
    try:
        if not os.path.exists(file_csv):
            return "Nessun CSV trovato sul server"
            
        df = pd.read_csv(file_csv)
        squadre_uniche = list(set(df['HomeTeam'].unique()) | set(df['AwayTeam'].unique()))
        
        # Corrispondenza flessibile per i nomi (Bet365 vs CSV)
        match_casa = get_close_matches(casa_live, squadre_uniche, n=1, cutoff=0.6)
        match_trasferta = get_close_matches(trasferta_live, squadre_uniche, n=1, cutoff=0.6)
        
        if match_casa and match_trasferta:
            nome_csv_casa = match_casa[0]
            nome_csv_trasferta = match_trasferta[0]
            
            # Filtra i dati storici delle due squadre
            df_casa = df[df['HomeTeam'] == nome_csv_casa]
            df_trasferta = df[df['AwayTeam'] == nome_csv_trasferta]
            
            if len(df_casa) > 0 and len(df_trasferta) > 0:
                media_gol_fatti_casa = df_casa['FTHG'].mean()
                media_gol_subiti_trasferta = df_trasferta['FTAG'].mean()
                proiezione = (media_gol_fatti_casa + media_gol_subiti_trasferta) / 2
                
                if proiezione > 1.5:
                    return f"Consiglio: Over 0.5 HT / Over 1.5 (Proiezione: {round(proiezione, 2)})"
                return "Consiglio: Valutare Live"
        return "Squadre non identificate accuratamente nell'archivio"
    except Exception as e:
        return f"Errore analisi: {str(e)}"

# =====================================================================
# 📩 FUNZIONE INVIO MESSAGGI TELEGRAM
# =====================================================================
def invia_telegram(messaggio):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": messaggio, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Errore invio Telegram: {e}")

# =====================================================================
# 🔄 CICLO DI ELABORAZIONE DATI LIVE (BET365)
# =====================================================================
def elabora_match_live(match):
    """
    Riceve i dati di una partita live, calcola i parametri
    e decide se inviare l'allarme su Telegram.
    """
    try:
        campionato = match.get("campionato", "Sconosciuto")
        casa = match.get("home", "Casa")
        trasferta = match.get("away", "Trasferta")
        minuto = int(match.get("minuto", 0))
        
        # Recupero statistiche correnti dal live
        stats = match.get("stats", {})
        attacchi_pericolosi = int(stats.get("attacks_dangerous_home", 0)) + int(stats.get("attacks_dangerous_away", 0))
        tiri_totali = int(stats.get("shots_on_home", 0)) + int(stats.get("shots_off_home", 0)) + int(stats.get("shots_on_away", 0)) + int(stats.get("shots_off_away", 0))
        tiri_porta_totali = int(stats.get("shots_on_home", 0)) + int(stats.get("shots_on_away", 0))
        corner_totali = int(stats.get("corners_home", 0)) + int(stats.get("corners_away", 0))
        
        g_casa = match.get("goals_home", 0)
        g_trasferta = match.get("goals_away", 0)
        
        # Calcolo pressione (Attacchi Pericolosi al Minuto)
        ap_minuto = attacchi_pericolosi / minuto if minuto > 0 else 0
        
        # -----------------------------------------------------------------
        # 📊 RIGHE MODIFICATE CON I PARAMETRI DI TEST RICHIESTI
        # -----------------------------------------------------------------
        condizione_assedio = (ap_minuto >= 0.50 and minuto >= 10 and tiri_totali >= 3 and corner_totali >= 2)
        condizione_bombardamento = (tiri_porta_totali >= 5 and corner_totali >= 2)
        # -----------------------------------------------------------------
        
        if condizione_assedio or condizione_bombardamento:
            # Identifica il tipo di allarme da mostrare nel testo
            tipo_allarme = "🎯 BOMBARDAMENTO" if condizione_bombardamento else "🔥 ASSEDIO"
            
            # Cerca se abbiamo un archivio pronto per questo campionato
            sigla_csv = DIZIONARIO_CAMPIONATI.get(campionato)
            if sigla_csv:
                consiglio = analizza_e_consiglia(sigla_csv, casa, trasferta, minuto)
            else:
                consiglio = "Nessun CSV associato a questo campionato"
                
            if "No Bet" not in consiglio and "Nessun CSV" not in consiglio:
                msg = (
                    f"🔥 <b>MILLENIUM: GOL IMMINENTE (B365)</b> 🔥\n\n"
                    f"⚽ <b>Match:</b> {casa} - {trasferta}\n"
                    f"🏆 <b>Campionato:</b> {campionato}\n"
                    f"⏱️ <b>Minuto:</b> {minuto}' | <b>Score:</b> {g_casa}-{g_trasferta}\n"
                    f"⚡ <b>Stato:</b> {tipo_allarme}\n\n"
                    f"📊 <b>Dati Live:</b>\n"
                    f"• Calci d'Angolo: {corner_totali}\n"
                    f"• Tiri Totali: {tiri_totali} (In Porta: {tiri_porta_totali})\n"
                    f"• AP/Minuto: {round(ap_minuto, 2)}\n\n"
                    f"📚 <b>Analisi Archivio:</b>\n<i>{consiglio}</i>"
                )
                invia_telegram(msg)
                print(f"🚀 Segnale inviato per {casa} - {trasferta}")
                
    except Exception as e:
        print(f"Errore elaborazione match live: {e}")

# =====================================================================
# SIMULAZIONE AVVIO (Per i log di Render)
# =====================================================================
if __name__ == "__main__":
    print("🔄 Avvio scansione parite live da Bet365...")
    print("⚙️ Parametri caricati (Assedio AP >= 0.50 | Bombardamento Tiri Porta >= 5)")
    
    # Esempio finto per vedere se il codice compila ed esegue il test senza crashare
    match_test = {
        "campionato": "Inghilterra Championship",
        "home": "Sheffield Wednesday",
        "away": "Derby",
        "minuto": 15,
        "goals_home": 0,
        "goals_away": 0,
        "stats": {
            "attacks_dangerous_home": 5,
            "attacks_dangerous_away": 3,
            "shots_on_home": 2,
            "shots_off_home": 1,
            "shots_on_away": 0,
            "shots_off_away": 0,
            "corners_home": 2,
            "corners_away": 0
        }
    }
    elabora_match_live(match_test)
