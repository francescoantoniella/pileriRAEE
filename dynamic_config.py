import json
import os
from datetime import datetime

CONFIG_FILE = "dynamic_config.json"

# Configurazione di default
DEFAULT_CONFIG = {
    "opcua_server_url": "opc.tcp://192.168.1.2:4840",
    "opcua_namespace_index": 2,
    "opcua_tag_prefix": "Siemens S7-1200/S7-1500.Tags.",
    "default_cer": 160214,
    "auto_increment_commessa": True,
    "auto_send_to_plc": True,
    "mode": "opcua",  # opcua, standalone
    "last_modified": None
}

def load_config():
    """Carica la configurazione dinamica"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Assicurati che tutti i campi di default siano presenti
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            print(f"Errore nel caricamento della configurazione: {e}")
    
    # Se il file non esiste, crea quello di default
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """Salva la configurazione dinamica"""
    config["last_modified"] = datetime.now().isoformat()
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Errore nel salvataggio della configurazione: {e}")
        return False

def update_config(updates):
    """Aggiorna la configurazione con nuovi valori"""
    config = load_config()
    config.update(updates)
    return save_config(config)

def get_config_value(key, default=None):
    """Ottiene un valore dalla configurazione"""
    config = load_config()
    return config.get(key, default)

def set_config_value(key, value):
    """Imposta un valore nella configurazione"""
    config = load_config()
    config[key] = value
    return save_config(config) 