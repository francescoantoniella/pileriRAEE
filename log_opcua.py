#!/usr/bin/env python3
"""
Test script per verificare la connessione OPC UA
"""

import sys
import time
from opcua_reader import OpcuaReader
from config import *
import json

import csv
import os
from datetime import datetime

def datalog(data):
    # Ottiene la data odierna nel formato ANNO-MESE-GIORNO
    data_oggi = datetime.now().strftime("%Y-%m-%d")
    # Crea il nome del file dinamicamente
    file_path = f"data_{data_oggi}.log"

    # Definiamo l'ordine dei campi (le chiavi del dizionario)
    fieldnames = [
        'timestamp', 'Commessa RX', 'Codice CER RX', 'Codice CER TX', 
        'Commessa TX', 'Ore totali commessa TX', 'Minuti totali commessa TX', 
        'Ore lavorate commessa TX', 'Minuti lavorati commessa TX', 'Potenza consumata TX'
    ]
    
    # Controlliamo se il file esiste già e se ha una dimensione > 0
    file_exists = os.path.isfile(file_path) and os.path.getsize(file_path) > 0

    with open(file_path, mode='a', newline='', encoding='utf-8') as file:
        # DictWriter usa le chiavi del dizionario per scrivere nelle colonne giuste
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # Se il file è vuoto o non esiste, scrive l'intestazione
        if not file_exists:
            writer.writeheader()
        
        # Scrive la riga con i dati del dizionario
        writer.writerow(data)


#def datalog(data):
#    with open("data.log", "a") as file:
#        file.write(json.dumps(data) + "\n")  # Aggiunge i dati e va a capo
def test_opcua_connection():
    try:
        # Crea il reader OPC UA
        reader = OpcuaReader(
            server_url=OPCUA_SERVER_URL,
            tag_names=TAG_LIST,
            tag_check=TAG_CHECK,
            namespace_index=OPCUA_NAMESPACE_INDEX,
            tag_prefix=OPCUA_TAG_PREFIX,
            on_change_callback=None,
            on_read_callback=datalog,
            interval=1.0
        )
        
        print(f"🔗 Tentativo di connessione a: {OPCUA_SERVER_URL}")
        
        # Prova a connettersi
#        reader.connect()
        
        print("✅ Connessione riuscita!")
        
        # Prova a leggere i dati
        print("📖 Lettura dati...")
        reader.start_polling()
        while 1:
            pass
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False



if __name__ == "__main__":
    success = test_opcua_connection()
    sys.exit(1) 
