#!/usr/bin/env python3
"""
Test script per verificare la connessione OPC UA
"""

import sys
import time
from opcua_reader import OpcuaReader
from config import *

def test_opcua_connection():
    """Test della connessione OPC UA"""
    print("🧪 Test Connessione OPC UA")
    print("=" * 40)
    
    try:
        # Crea il reader OPC UA
        reader = OpcuaReader(
            server_url=OPCUA_SERVER_URL,
            tag_names=TAG_LIST,
            tag_check=TAG_CHECK,
            namespace_index=OPCUA_NAMESPACE_INDEX,
            tag_prefix=OPCUA_TAG_PREFIX,
            on_change_callback=None,
            interval=1.0
        )
        
        print(f"🔗 Tentativo di connessione a: {OPCUA_SERVER_URL}")
        
        # Prova a connettersi
        reader.connect()
        
        print("✅ Connessione riuscita!")
        
        # Prova a leggere i dati
        print("📖 Lettura dati...")
        for i in range(3):
            data = reader.read_one()
            print(f"   Lettura {i+1}: {data}")
            time.sleep(1)
        
        # Prova a scrivere (simulazione)
        print("✍️  Test scrittura...")
        success = reader.write_tags(12345, 160214)
        if success:
            print("✅ Scrittura riuscita!")
        else:
            print("❌ Errore nella scrittura")
        
        # Disconnetti
        reader.disconnect()
        print("🔌 Disconnesso")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        print("\n💡 Possibili cause:")
        print("   - Server OPC UA non raggiungibile")
        print("   - URL errato in config.py")
        print("   - Firewall che blocca la connessione")
        print("   - Namespace o tag prefix errati")
        return False

if __name__ == "__main__":
    success = test_opcua_connection()
    if success:
        print("\n🎉 Test completato con successo!")
        print("Il sistema OPC UA è configurato correttamente.")
    else:
        print("\n⚠️  Test fallito!")
        print("Verifica la configurazione in config.py")
        sys.exit(1) 