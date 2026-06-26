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
# 🧠 FUNZIONE ANALISI STORICO (CON FRINGE MATCHING SQUADRE)
# =====================================================================
def analizza_e_consiglia(file_csv, casa_live, trasferta_live, minuto):
    try:
        if not os.path.exists(file_csv):
            return "Nessun CSV trovato sul server"
            
        df = pd.read_csv(file_csv)
        squadre_uniche = list(set(df['HomeTeam'].unique()) | set(df['AwayTeam'].unique()))
        
        match_casa = get_close_matches(casa_live, squadre_uniche, n=1, cutoff=0.6)
        match_trasferta = get_close_matches(trasferta_live, squadre_uniche, n=1, cutoff=0.6)
        
        if match_casa and match_trasferta:
            nome_csv_casa = match_casa[0]
            nome_csv_trasferta = match_trasferta[0]
            
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
# 🔄 ELABORAZIONE LIVE MATCH
# =====================================================================
def elabora_match_live(match):
    try:
        campionato = match.get("campionato", "Sconosciuto")
        casa = match.get("home", "Casa")
        trasferta = match.get("away", "Trasferta")
        minuto = int(match.get("minuto", 0))
        
        stats = match.get("stats", {})
        attacchi_pericolosi_casa = int(stats.get("attacks_dangerous_home", 0))
        attacchi_pericolosi_trasferta = int(stats.get("attacks_dangerous_away", 0))
        attacchi_pericolosi_totali = attacchi_pericolosi_casa + attacchi_pericolosi_trasferta
        
        tiri_totali = int(stats.get("shots_on_home", 0)) + int(stats.get("shots_off_home", 0)) + int(stats.get("shots_on_away", 0)) + int(stats.get("shots_off_away", 0))
        tiri_porta_totali = int(stats.get("shots_on_home", 0)) + int(stats.get("shots_on_away", 0))
        corner_totali = int(stats.get("corners_home", 0)) + int(stats.get("corners_away", 0))
        
        g_casa = match.get("goals_home", 0)
        g_trasferta = match.get("goals_away", 0)
        
        # Calcolo Pressione usando il nome esatto della tua variabile originale
        attacchi_pericolosi_al_minuto = attacchi_pericolosi_totali / minuto if minuto > 0 else 0
        
        # -----------------------------------------------------------------
        # 🎯 RIGHE AGGIORNATE CON ALLINEAMENTO E VARIABILI CORRETTE
        # -----------------------------------------------------------------
        condizione_assedio = (attacchi_pericolosi_al_minuto >= 0.50 and minuto >= 10 and tiri_totali >= 3 and corner_totali >= 2)
        condizione_bombardamento = (tiri_porta_totali >= 5 and corner_totali >= 2)
        # -----------------------------------------------------------------
        
        if condizione_assedio or condizione_bombardamento:
            tipo_allarme = "🎯 BOMBARDAMENTO" if condizione_bombardamento else "🔥 ASSEDIO"
            
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
                    f"• AP/Minuto: {round(attacchi_pericolosi_al_minuto, 2)}\n\n"
                    f"📚 <b>Analisi Archivio:</b>\n<i>{consiglio}</i>"
                )
                invia_telegram(msg)
                print(f"🚀 Segnale inviato per {casa} - {trasferta}")
                
    except Exception as e:
        print(f"Errore elaborazione match live: {e}")

# =====================================================================
# 🔄 LOOP INFINITO REALE PER RENDER
# =====================================================================
if __name__ == "__main__":
    print("🤖 MILLENIUM BOT ATTIVO IN BACKGROUND...")
    
    while True:
        try:
            print("🔄 Avvio scansione partite live da Bet365...")
            
            # (Qui l'integrazione con il tuo sistema reale per scaricare i match)
            # esempio: 
            # elenco_partite = scarica_live()
            # for match in elenco_partite:
            #     elabora_match_live(match)
            
            time.sleep(60) 
            
        except Exception as e:
            print(f"Errore nel ciclo continuo: {e}")
            time.sleep(10)
