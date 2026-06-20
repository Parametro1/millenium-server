def analizza_e_consiglia(nome_file_csv, casa_live, ospite_live, minuto=None, gol_totali=0, is_live=False):
    file_standard = f"{nome_file_csv}.csv"
    file_maiuscolo = f"{nome_file_csv}.CSV"
    nome_file = file_standard if os.path.exists(file_standard) else file_maiuscolo
    
    if not os.path.exists(nome_file):
        return "Nessun CSV trovato."
    
    try:
        df = pd.read_csv(nome_file)
        # Filtro squadre
        partite_casa = df[df['HomeTeam'].str.contains(casa_live, case=False, na=False)]
        partite_ospite = df[df['AwayTeam'].str.contains(ospite_live, case=False, na=False)]
        
        # Calcolo Medie Gol
        media_gol = (partite_casa['FTHG'].mean() if not partite_casa.empty else 0.0) + \
                    (partite_ospite['FTAG'].mean() if not partite_ospite.empty else 0.0)
        
        # Calcolo Medie Corner (Nuova Logica Pro)
        media_corner = (partite_casa['HC'].mean() if not partite_casa.empty and 'HC' in df.columns else 0.0) + \
                       (partite_ospite['AC'].mean() if not partite_ospite.empty and 'AC' in df.columns else 0.0)
        
        output = f"Gol: {media_gol:.2f} | Corner: {media_corner:.1f} | "
        
        if is_live and minuto is not None:
            consiglio_gol = "No Bet"
            if media_gol >= 2.40:
                if minuto <= 35: consiglio_gol = "OVER 0.5 HT"
                elif minuto <= 65: consiglio_gol = f"OVER {gol_totali + 1.5} LIVE"
                elif minuto <= 82: consiglio_gol = f"OVER {gol_totali + 0.5} FINALE"
            
            # Logica Corner Pro
            consiglio_corner = ""
            if media_corner >= 9.5:
                consiglio_corner = " + OVER CORNER"
                
            if consiglio_gol != "No Bet":
                output += f"<span style='color:#10b981;font-weight:bold;'>{consiglio_gol}{consiglio_corner}</span>"
            else:
                output += "No Bet"
        else:
            output += "STUDIO: Analisi pronta."
            
        return output
    except Exception:
        return "Errore calcolo Pro."
