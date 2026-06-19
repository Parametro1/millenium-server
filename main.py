# Pagina web sostitutiva leggera che non si interrompe
            html = """<!DOCTYPE html>
            <html>
            <head><title>Millenium Terminal</title></style></head>
            <body style="background:#010409; color:#c9d1d9; font-family:sans-serif; padding:20px;">
                <h1>Millenium Bot — Status Active</h1>
                <p>Il motore di scansione sta girando in background.</p>
            </body>
            </html>"""
            self.wfile.write(html.encode("utf-8"))
            return

def invia_telegram(messaggio):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        try:
            requests.post(url, json={"chat_id": CHAT_ID, "text": messaggio, "parse_mode": "Markdown"})
        except Exception as e:
            print(f"Errore Telegram: {e}", flush=True)

def analizza_archivio_storico(nome_file_csv, casa_live, ospite_live):
    file_standard = f"{nome_file_csv}.csv"
    if os.path.exists(file_standard):
        try:
            df = pd.read_csv(file_standard)
            partite_casa = df[df['HomeTeam'].str.contains(casa_live, case=False, na=False)]
            partite_ospite = df[df['AwayTeam'].str.contains(ospite_live, case=False, na=False)]
            if not partite_casa.empty and not partite_ospite.empty:
                media_casa = partite_casa['FTHG'].mean()
                media_ospite = partite_ospite['FTAG'].mean()
                return f"\n🏠 {casa_live} Media Gol: {media_casa:.2f}\n🚀 {ospite_live} Media Gol: {media_ospite:.2f}"
        except: pass
    return "\n⚠️ Dati storici non disponibili."

def scansione_partite():
    print("Scansione partite live in corso...", flush=True)
    try:
        response = session.get(URL_LIVE, timeout=10)
        if response.status_code == 200:
            partite = response.json().get("Value", [])
            for partita in partite:
                campionato_live = partita.get("LEAG", "")
                squadra_casa = partita.get("O1", "")
                squadra_ospite = partita.get("O2", "")
                
                if campionato_live in DIZIONARIO_CAMPIONATI:
                    nome_file_csv = DIZIONARIO_CAMPIONATI[campionato_live]
                    
                    # Estrazione semplificata e sicura dei tiri
                    stats = partita.get("SC", {}).get("S", [])
                    tiri_totali_live = 0
                    for s in stats:
                        if s.get("Type") == 2: # ID standard tiri in porta
                            tiri_totali_live = int(s.get("All1", 0)) + int(s.get("All2", 0))
                    
                    if tiri_totali_live >= 5:
                        analisi = analizza_archivio_storico(nome_file_csv, squadra_casa, squadra_ospite)
                        messaggio = f"⚽ *MILLENIUM BOT - VALUE BET*\n🏆 {campionato_live}\n⚔️ {squadra_casa} vs {squadra_ospite}\n🔥 Tiri in porta: {tiri_totali_live}{analisi}"
                        invia_telegram(messaggio)
                        print(f"Segnale inviato per {squadra_casa}", flush=True)
                        time.sleep(2)
    except Exception as e:
        print(f"Errore screening: {e}", flush=True)

# Avvio reale dei processi separati
Thread(target=start_server, daemon=True).start()
print("Millenium Bot avviato correttamente!", flush=True)

while True:
    scansione_partite()
    time.sleep(60)
