import os
import time
import requests
import pandas as pd
from threading import Thread
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

# Porta dinamica per Render
def avvia_server():
    porta = int(os.environ.get("PORT", 10000))
    print("Server avviato sulla porta " + str(porta))
    with TCPServer(("0.0.0.0", porta), SimpleHTTPRequestHandler) as server:
        server.serve_forever()

def analizza_csv_test():
    # Funzione di test per verificare se legge i file CSV
    files = [f for f in os.listdir('.') if f.endswith('.csv')]
    print("File CSV trovati nel server: " + str(files))
    if len(files) > 0:
        try:
            df = pd.read_csv(files[0])
            print("Lettura riuscita del file: " + files[0])
            print("Colonne trovate: " + str(df.columns.tolist()))
        except Exception as e:
            print("Errore nella lettura del CSV: " + str(e))

if __name__ == "__main__":
    Thread(target=avvia_server, daemon=True).start()
    print("Millenium Bot Analisi V3 avviato...")
    
    # Test lettura file
    analizza_csv_test()
    
    while True:
        time.sleep(60)
