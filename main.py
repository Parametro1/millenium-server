import os
import time
import requests
from threading import Thread
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

def avvia_server():
    porta = int(os.environ.get("PORT", 10000))
    print(f"Server avviato sulla porta {porta}")
    with TCPServer(("0.0.0.0", porta), SimpleHTTPRequestHandler) as server:
        server.serve_forever()

if __name__ == "__main__":
    # Avvia il server web
    Thread(target=avvia_server, daemon=True).start()
    print("Millenium Bot Online. In attesa di segnali...")
    
    # Loop di mantenimento
    while True:
        time.sleep(60)
