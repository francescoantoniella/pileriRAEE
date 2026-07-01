import os

# Configurazione del database
DATABASE_PATH = "telemetria_ricostruita.db"

# Conversione valore raw (Potenza consumata TX / energia_*_wh) → kWh
# Il PLC fornisce un progressivo in unità tali che: valore_raw / RAW_TO_KWH = kWh
RAW_TO_KWH = 100

# Configurazione OPC UA
OPCUA_SERVER_URL = "opc.tcp://192.168.1.2:4840"
OPCUA_NAMESPACE_INDEX = 2
OPCUA_TAG_PREFIX = "Siemens S7-1200/S7-1500.Tags."

# Configurazione del server web
WEB_HOST = "0.0.0.0"  # in locale usa localhost; in produzione impostare "0.0.0.0"
WEB_PORT = 80        # 8080 per test senza root; in produzione usare 80 (richiede sudo)
WEB_DEBUG = True

# Configurazione del polling
POLLING_INTERVAL = 2.0

# Lista dei tag
TAG_LIST = [
    "Commessa RX",
    "Codice CER RX", 
    "Codice CER TX",
    "Commessa TX",
    "Ore totali commessa TX",
    "Minuti totali commessa TX",
    "Ore lavorate commessa TX",
    "Minuti lavorati commessa TX",
    "Potenza consumata TX"]

# Tag da monitorare per i cambiamenti
TAG_CHECK = ['Commessa TX', 'Commessa RX']

# Modalità di default
DEFAULT_MODE = "standalone"

# Configurazioni per la robustezza del sistema
POLLER_MAX_RETRIES = 3
POLLER_RETRY_DELAY = 10  # secondi
POLLER_CONNECTION_TIMEOUT = 30  # secondi

def get_mode_from_env():
    """Ottiene la modalità dalle variabili d'ambiente"""
    return os.environ.get('OPC_LOGGER_MODE', DEFAULT_MODE)

def is_opcua_mode():
    """Verifica se è attiva la modalità OPC UA"""
    return get_mode_from_env() == "opcua" 
