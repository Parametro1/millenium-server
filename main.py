import os
import csv
import time
import requests
import numpy as np
from scipy.stats import poisson

# =====================================================================
# CONFIGURAZIONE COMPLETA (API E CSV)
# =====================================================================
MIA_API_KEY = "6ecd40bd18c885456522ea6cd79d195a"
URL_THE_ODDS_API = "https://api.the-odds-api.com/v4/sports/soccer/odds/" 

# Render manterrà il tuo file D1 (1).csv nella stessa cartella senza toccarlo
CSV_FILE_NAME = "D1 (1).csv"  

class SistemaTipsterProAI:
    def __init__(self):
        self.team_stats = {}
        self.league_avg_goals = 1.45  

    def carica_archivio_csv(self, percorso_file):
        """Legge direttamente il tuo file D1 (1).csv ed estrae i parametri delle squadre"""
        if not os.path.exists(percorso_file):
            print(f"⚠️ Archivio CSV '{percorso_file}' non trovato nei file di Render!")
            return False
            
        try:
            # Calcoliamo prima le medie del campionato dal tuo file reale
            gol_casa_tot, gol_trasf_tot, match_tot = 0, 0, 0
            with open(percorso_file, mode='r', encoding='utf-8') as f:
                lettore = csv.DictReader(f)
                righe = list(lettore)
                for riga in righe:
                    if riga.get('FTHG') and riga.get('FTAG'):
                        gol_casa_tot += float(riga['FTHG'])
                        gol_trasf_tot += float(riga['FTAG'])
                        match_tot += 1
            
            media_campionato_gol = (gol_casa_tot + gol_trasf_tot) / (match_tot * 2) if match_tot > 0 else 1.45
            self.league_avg_goals = media_campionato_gol

            # Mappiamo i dati delle squadre dal tuo storico
            squadre_data = {}
            for riga in righe:
                if not riga.get('HomeTeam'): continue
                hc, ac = riga['HomeTeam'].strip(), riga['AwayTeam'].strip()
                fthg, ftag = float(riga['FTHG']), float(riga['FTAG'])
                
                if hc not in squadre_data: squadre_data[hc] = {'gf_c': [], 'gs_c': [], 'gf_t': [], 'gs_t': []}
                if ac not in squadre_data: squadre_data[ac] = {'gf_c': [], 'gs_c': [], 'gf_t': [], 'gs_t': []}
                
                squadre_data[hc]['gf_c'].append(fthg)
                squadre_data[hc]['gs_c'].append(ftag)
                squadre_data[ac]['gf_t'].append(ftag)
                squadre_data[ac]['gs_t'].append(fthg)

            for sq, d in squadre_data.items():
                self.team_stats[sq] = {
                    'att_casa': np.mean(d['gf_c']) / media_campionato_gol if d['gf_c'] else 1.0,
                    'def_casa': np.mean(d['gs_c']) / media_campionato_gol if d['gs_c'] else 1.0,
                    'att_trasferta': np.mean(d['gf_t']) / media_campionato_gol if d['gf_t'] else 1.0,
                    'def_trasferta': np.mean(d['gs_t']) / media_campionato_gol if d['gs_t'] else 1.0
                }
            print(f"✅ Archivio storico '{percorso_file}' elaborato: {len(self.team_stats)} squadre pronte.")
            return True
        except Exception as e:
            print(f"❌ Errore elaborazione CSV: {e}")
            return False

    def analizza_match_live_odds(self, casa, trasferta, minuto=0):
        sq_c = self.team_stats.get(casa, {'att_casa': 1.0, 'def_casa': 1.0, 'att_trasferta': 1.0, 'def_trasferta': 1.0})
        sq_t = self.team_stats.get(trasferta, {'att_casa': 1.0, 'def_casa': 1.0, 'att_trasferta': 1.0, 'def_trasferta': 1.0})
        
        lambda_base = sq_c['att_casa'] * sq_t['def_trasferta'] * self.league_avg_goals
        mu_base = sq_t['att_trasferta'] * sq_c['def_casa'] * self.league_avg_goals
        
        frazione_tempo = max(0, 90 - minuto) / 90.0
        lambda_residuo = lambda_base * frazione_tempo
        mu_residuo = mu_base * frazione_tempo
        
        prob_1 = 0.0
        for i in range(6):
            for j in range(6):
                p_cella = poisson.pmf(i, lambda_residuo) * poisson.pmf(j, mu_residuo)
                if i > j: prob_1 += p_cella
                    
        return {"1": round(1 / prob_1, 2) if prob_1 > 0.01 else 99.0}

    def calcola_dropping_odds_e_filtra(self, quota_apertura, quota_attuale):
        delta_q = (quota_attuale - quota_apertura) / quota_apertura
        return round(delta_q * 100, 2), delta_q < -0.08

    def calcola_kelly_frazionario(self, prob_reale, quota_bookmaker):
        b = quota_bookmaker - 1
        kelly_puro = (prob_reale * b - (1 - prob_reale)) / b
        return round(max(0.0, kelly_puro * 0.25) * 100, 2)

    def validazione_ordine_hedge_fund(self, quota_reale, quota_apertura, quota_attuale, bankroll_totale):
        prob_reale = 1 / quota_reale
        delta_p, mercato_bruciato = self.calcola_dropping_odds_e_filtra(quota_apertura, quota_attuale)
        
        if mercato_bruciato or quota_attuale <= quota_reale:
            return {"Stato": "REJECTED"}
        
        stake_p = self.calcola_kelly_frazionario(prob_reale, quota_attuale)
        capitale = round((stake_p / 100) * bankroll_totale, 2)
        
        if stake_p > 0:
            return {"Stato": "APPROVED", "Delta Q": f"{delta_p}%", "Quota AI": quota_reale, "Quota Banco": quota_attuale, "Stake": f"{stake_p}%", "Capitale": f"{capitale}€"}
        return {"Stato": "REJECTED"}

# =====================================================================
# MOTORE DI SCANSIONE OPERATIVO
# =====================================================================
def esegui_scansione_fondi(bankroll=10000):
    ai_system = SistemaTipsterProAI()
    if not ai_system.carica_archivio_csv(CSV_FILE_NAME): return
    
    params = {'apiKey': MIA_API_KEY, 'regions': 'eu', 'markets': 'h2h', 'oddsFormat': 'decimal'}
    
    print("\n🔄 Connessione a The Odds API...")
    try:
        risposta = requests.get(URL_THE_ODDS_API, params=params, timeout=12)
        if risposta.status_code == 200:
            partite = risposta.json()
            print(f"📊 Scansione in corso su {len(partite)} match totali...")
            for match in partite:
                casa, trasferta = match['home_team'], match['away_team']
                
                if match.get('bookmakers'):
                    primo_bkr = match['bookmakers'][0]
                    nome_bkr = primo_bkr['title']
                    market_h2h = primo_bkr['markets'][0]['outcomes']
                    
                    quota_bkr_1 = 1.0
                    for outcome in market_h2h:
                        if outcome['name'] == casa: quota_bkr_1 = outcome['price']
                    
                    quote_reali_ai = ai_system.analizza_match_live_odds(casa, trasferta, minuto=0)
                    quota_equa_1 = quote_reali_ai["1"]
                    quota_apertura_ipotetica = quota_bkr_1 + 0.12
                    
                    decisione = ai_system.validazione_ordine_hedge_fund(quota_equa_1, quota_apertura_ipotetica, quota_bkr_1, bankroll)
                    
                    if decisione['Stato'] == "APPROVED":
                        print(f"\n🔥 [SEGNALE APPROVATO] -> {casa} vs {trasferta} ({nome_bkr})")
                        print(f"   Quota AI: {decisione['Quota AI']} | Quota Banco: {decisione['Quota Banco']} | Delta: {decisione['Delta Q']}")
                        print(f"   💰 Investimento consigliato Kelly: {decisione['Capitale']} ({decisione['Stake']})")
            print("\n🏁 Scansione terminata con successo.")
    except Exception as e:
        print(f"⚠️ Errore scansione: {e}")

if __name__ == "__main__":
    esegui_scansione_fondi(bankroll=10000)
