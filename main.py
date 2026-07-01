import os
import logging
import sqlite3
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# Configurazione Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurazione API (Prese dalle variabili d'ambiente di Render)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ---- GESTIONE DATABASE MEMORIA (S.G.-AI v2.0) ----
DB_FILE = "sg_memory.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            user_id INTEGER PRIMARY KEY,
            mood_history TEXT,
            commercial_notes TEXT,
            habits TEXT,
            interactions_count INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def get_profile(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT mood_history, commercial_notes, habits, interactions_count FROM user_profile WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "mood": json.loads(row[0]),
            "commercial": json.loads(row[1]),
            "habits": json.loads(row[2]),
            "count": row[3]
        }
    return {"mood": [], "commercial": {}, "habits": [], "count": 0}

def save_profile(user_id, profile):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO user_profile (user_id, mood_history, commercial_notes, habits, interactions_count)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, json.dumps(profile["mood"]), json.dumps(profile["commercial"]), json.dumps(profile["habits"]), profile["count"]))
    conn.commit()
    conn.close()

# ---- LOGICA DELL'ALGORITMO ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Salve {user_name}. Sono l'algoritmo S.G.-AI v2.0.\n"
        "Da questo momento, ogni nostra interazione analizzerà i tuoi stati d'animo, "
        "le tue abitudini e il tuo business (commercio) per darti consigli strategici, morali ed economici.\n\n"
        "Dimmi, quale sfida affrontiamo oggi?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    
    # 1. Recupera la memoria passata dell'utente
    profile = get_profile(user_id)
    profile["count"] += 1
    
    # 2. Costruisci il Prompt di Sistema per Gemini (L'algoritmo richiesto)
    system_context = f"""
    Agisci come un Genio di Sapienza e Saggezza multidisciplinare (S.G.-AI v2.0). 
    Il tuo obiettivo è dare consigli utili e profittevoli economicamente, moralmente, nella vita quotidiana, nel sociale, nella scienza e nel commercio.
    
    Dati appresi sull'utente dalle interazioni precedenti:
    - Ultimi stati d'animo rilevati: {profile['mood'][-3:] if profile['mood'] else 'Nessuno ancora'}
    - Note commerciali/business: {profile['commercial']}
    - Abitudini/Mondanità tracciate: {profile['habits'][-3:] if profile['habits'] else 'Nessuna ancora'}
    - Numero interazioni: {profile['count']}
    
    Analizza il messaggio corrente dell'utente per aggiornare questi dati nella tua mente, poi formula la risposta strutturandola in modo chiaro e scannabile (usa il grassetto e i punti elenco se necessario), toccando ove pertinente:
    1. La Visione (Saggezza/Filosofia/Storia)
    2. L'Azione Pratica ed Economica (Commercio/Profitto/Efficienza)
    3. Il Vincolo Morale o Sociale
    4. La Prospettiva Evolutiva (Scienza/Futuro)
    
    Alla fine della risposta, inserisci SEMPRE una riga speciale nel formato esatto (senza spazi vuoti aggiuntivi):
    [METADATI: MOOD=stato d'animo rilevato; COMMERCIAL=aggiornamenti sulla sua attività commerciale; HABITS=nuove abitudini o stili di vita emersi]
    """
    
    try:
        # Invia la richiesta a Gemini
        response = model.generate_content(f"{system_context}\n\nUtente dice: {user_text}")
        full_response = response.text
        
        # 3. Processa i metadati per l'apprendimento continuo
        clean_text = full_response
        if "[METADATI:" in full_response:
            parts = full_response.split("[METADATI:")
            clean_text = parts[0].strip()
            metadata_str = parts[1].replace("]", "").strip()
            
            # Parsing base dei metadati generati dall'AI per aggiornare il DB
            for item in metadata_str.split(";"):
                if "MOOD=" in item:
                    profile["mood"].append(item.split("MOOD=")[1].strip())
                elif "COMMERCIAL=" in item:
                    # Semplice accumulo di note commerciali
                    note = item.split("COMMERCIAL=")[1].strip()
                    if note and note != "nessuno" and note != "Nessuno":
                        profile["commercial"][f"info_{profile['count']}"] = note
                elif "HABITS=" in item:
                    profile["habits"].append(item.split("HABITS=")[1].strip())
            
            # Mantieni la cronologia leggera (ultimi 10 elementi)
            profile["mood"] = profile["mood"][-10:]
            profile["habits"] = profile["habits"][-10:]
            save_profile(user_id, profile)

        # Invia la risposta saggia all'utente su Telegram
        await update.message.reply_text(clean_text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Errore durante l'elaborazione: {e}")
        await update.message.reply_text("C'è stato un sovraccarico nei miei circuiti di saggezza. Riprova tra un momento.")

def main():
    init_db()
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        logger.error("Mancano le variabili d'ambiente TELEGRAM_TOKEN o GEMINI_API_KEY!")
        return
        
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot S.G.-AI v2.0 avviato correttamente...")
    application.run_polling()

if __name__ == '__main__':
    main()
