# OPC Logger

Sistema di logging per dati OPC UA con interfaccia web.

## Installazione

### Installazione Base (Modalità Standalone)
```bash
# Installa solo le dipendenze essenziali
pip install -r requirements.txt

# Oppure installa manualmente
pip install bottle reportlab
```

### Installazione Completa (Con Supporto OPC UA)
```bash
# Installa tutte le dipendenze incluse quelle per OPC UA
pip install -r requirements-opcua.txt
```

### Note sulle Dipendenze
- **Modalità Standalone**: Solo `bottle` e `reportlab` (2 pacchetti)
- **Modalità OPC UA**: Tutte le dipendenze per la connessione OPC UA (~25 pacchetti)
- **Funzionalità**: Il sistema funziona in entrambe le modalità

## Caratteristiche

- **Robustezza**: Il sistema continua a funzionare anche quando OPC UA non è disponibile
- **Accesso ai dati**: I dati salvati sono sempre accessibili tramite l'interfaccia web
- **Retry automatico**: Tentativi automatici di riconnessione al server OPC UA
- **Modalità standalone**: Funzionamento senza connessione OPC UA
- **API REST**: Interfaccia programmatica per l'accesso ai dati
- **Esportazione CSV**: Esportazione dei dati in formato CSV
- **Gestione Commesse**: Interfaccia per impostare commessa e codice CER
- **Incremento Automatico**: Preimpostazione automatica della commessa successiva

## Modalità di funzionamento

### Modalità OPC UA
```bash
# Installa le dipendenze OPC UA
pip install -r requirements-opcua.txt

# Avvia in modalità OPC UA
python server.py opcua

# Oppure con variabile d'ambiente
export OPC_LOGGER_MODE=opcua
python server.py
```

### Modalità Standalone (default)
```bash
# Installa solo le dipendenze essenziali
pip install -r requirements.txt

# Avvia in modalità standalone
python server.py standalone
# oppure
python server.py
```

### Configurazione OPC UA
Modifica `config.py` per personalizzare:
- `OPCUA_SERVER_URL`: URL del server OPC UA
- `OPCUA_NAMESPACE_INDEX`: Indice del namespace
- `OPCUA_TAG_PREFIX`: Prefisso dei tag
- `TAG_LIST`: Lista dei tag da monitorare

### Test Connessione OPC UA
```bash
# Test della connessione OPC UA
python test_opcua.py

# Se il test fallisce, verifica:
# - URL del server in config.py
# - Connessione di rete
# - Firewall
# - Configurazione del server OPC UA
```

### Pulizia Directory
```bash
# Pulisci file temporanei e di sviluppo
./clean_directory.sh

# Oppure manualmente:
rm -rf __pycache__/
rm test_standalone.py opcua_reader_sim.py record.json
rmdir static/ 2>/dev/null || true
```

## Visualizzazione Dati

### Home Page
- **Default**: 10 record più recenti
- **Personalizzazione**: `http://localhost:8080/?n=25` per vedere 25 record
- **Limiti**: Minimo 1, massimo 100 record
- **Link rapidi**: 10, 25, 50, 100 record disponibili nell'interfaccia

### API
- **Default**: 5 record più recenti
- **Personalizzazione**: `GET /api/commesse/recenti?n=25`
- **Risposta**: Include il numero di record restituiti

## API Endpoints

### Dati
- `GET /api/commesse/recenti?n=5` - Ultime n commesse
- `GET /api/commesse/tutte` - Tutte le commesse salvate
- `GET /api/export/csv` - Esportazione CSV dei dati

### Report
- `GET /report/giornaliero?data=YYYY-MM-DD` - Report giornaliero
- `GET /report/mensile?anno=YYYY&mese=MM` - Report mensile con statistiche
- `GET /report/annuale?anno=YYYY` - Report annuale con statistiche
- `GET /api/report/giornaliero?data=YYYY-MM-DD` - API report giornaliero
- `GET /api/report/mensile?anno=YYYY&mese=MM` - API report mensile
- `GET /api/report/annuale?anno=YYYY` - API report annuale

### Esportazione
- `GET /api/export/csv` - Esportazione CSV di tutti i dati
- `GET /api/export/pdf/giornaliero?data=YYYY-MM-DD` - PDF report giornaliero
- `GET /api/export/pdf/mensile?anno=YYYY&mese=MM` - PDF report mensile
- `GET /api/export/pdf/annuale?anno=YYYY` - PDF report annuale

### Controllo del sistema
- `GET /api/status` - Stato del sistema
- `POST /api/poller/start` - Avvia il poller
- `POST /api/poller/stop` - Ferma il poller
- `POST /api/poller/restart` - Riavvia il poller

### Impostazione commessa
- `POST /api/commessa/imposta` - Imposta commessa e CER
- `GET /api/commessa/ultima` - Ottiene l'ultima commessa utilizzata

## Gestione Commesse

### Interfaccia Web
- **Form dedicato**: Inserimento numero commessa e codice CER
- **Codici CER**: 160214 e 200000 disponibili in dropdown
- **Incremento automatico**: Pulsante "+1" per incrementare la commessa
- **Preimpostazione**: Caricamento automatico dell'ultima commessa + 1

### API
- **Impostazione**: `POST /api/commessa/imposta` con JSON `{"commessa": 123, "cer": 160214}`
- **Ultima commessa**: `GET /api/commessa/ultima` restituisce l'ultima commessa utilizzata

## Configurazione

Modifica `config.py`