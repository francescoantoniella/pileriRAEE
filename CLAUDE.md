# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Avvio dell'applicazione

```bash
# Modalità standalone (senza OPC UA)
python server.py
python server.py standalone

# Modalità OPC UA (collegamento al PLC Siemens S7-1200/S7-1500)
python server.py opcua

# Installazione dipendenze base
pip install -r reqirements.txt
```

La porta web di default è **80** (richiede sudo). Per sviluppo usare porta **8080** modificando `WEB_PORT` in `config.py`. Non esistono test automatici nel progetto.

## Architettura

L'applicazione è un server web **Bottle** che legge dati da un PLC via **OPC UA** e li persiste in **SQLite**. Lo stack è:

### `data_provider.py` — Astrazione sorgente dati
Classe base `DataProvider` con due implementazioni:
- `OpcuaReader` (`opcua_reader.py`): connette al PLC, legge/scrive tag, polling configurabile
- `StandaloneDataProvider`: provider mock che ritorna valori zero

Entrambe espongono `connect()`, `start_polling()`, `write_tags()`. Il polling chiama due callback registrate in `server.py`: `on_change()` (solo quando i valori cambiano) e `on_read()` (ad ogni lettura).

### `server.py` — Server web e logica di business
Il cuore dell'applicazione. Gestisce:
- **State machine commesse** nel callback `on_change()`: tre casi basati sui valori `commessa_rx` (dal PLC) e `commessa_tx` (trasmessa al PLC):
  - CRX≠0, CTX=0 → lavorazione iniziata, crea record, registra energia iniziale
  - CRX=CTX≠0 → fase registrazione, aggiorna dati operativi
  - CRX=0, CTX≠0 → lavorazione completata, registra energia finale, auto-incrementa
- **Log CSV giornalieri** (`data_YYYY-MM-DD.log`) via `datalog()`
- **API REST** per dashboard, report, configurazione runtime
- **Avvio robusto** del poller: retry automatico (3 tentativi, 10s di attesa), thread daemon

### `db.py` — Layer database
`TelemetriaDB`: wrapper SQLite3 per la tabella `telemetria`. Gestisce il ciclo di vita delle commesse, i calcoli energetici (`energia_iniziale_wh`, `energia_finale_wh`, `energia_consumata_wh`) e la generazione di report (giornaliero/mensile/annuale). Aggiunge automaticamente colonne mancanti a DB esistenti.

### Configurazione
- `config.py`: configurazione statica (URL OPC UA, nomi tag, `POLLING_INTERVAL`, `RAW_TO_KWH=100`, percorso DB)
- `dynamic_config.json`: configurazione runtime modificabile via API (URL server, `default_cer`, `auto_increment_commessa`, `auto_send_to_plc`, `mode`)
- `admin_password.txt`: password per le API di configurazione (default: `admin123`)

### Frontend
Template **Bottle** in `templates/` per i report. Dashboard principale in `templates/index.tpl` con JavaScript vanilla; i report PDF usano **ReportLab**.

## API principali

| Endpoint | Scopo |
|----------|-------|
| `GET /api/commesse/recenti?n=5` | Ultime commesse con dati energia |
| `POST /api/commessa/imposta` | Imposta manualmente commessa e codice CER |
| `GET /report/giornaliero?data=YYYY-MM-DD` | Report HTML giornaliero |
| `GET /api/export/pdf/mensile?anno=YYYY&mese=MM` | Report PDF mensile |
| `POST /api/poller/restart` | Riavvia il provider dati |
| `GET /api/config` | Legge configurazione corrente |
| `POST /api/config/update` | Aggiorna configurazione (richiede password) |

## Handover — sessione debug 2026-07-01

Contesto: l'utente segnalava che impostare una commessa non veniva più recepito dal PLC ("non la prende"), a differenza di prima del 24/06/2026. Analisi condotta anche direttamente sulla macchina di produzione `impiantoraee` (Raspberry Pi, ora raggiungibile anche via Claude Code installato lì; accesso SSH e credenziali sono salvati nella memoria di Claude Code, non in questo repo).

### Bug corretti in questa sessione

1. **`server.py` — `imposta_commessa()` non scriveva più al PLC.** Confrontando la working tree con la versione in staging/HEAD, la chiamata `poller.write_tags(commessa_rx, cer_rx)` era stata rimossa: l'endpoint aggiornava solo il DB locale, mai i tag OPC UA `Commessa RX` / `Codice CER RX` sul PLC. **Ripristinata** la chiamata (con relativo controllo `poller`/`poller_running` e gestione errore), mantenendo la logica di deduplicazione già presente (`db.commessa_esiste`).

2. **`db.py` — `TelemetriaDB` non era thread-safe.** `self.conn`/`self.cur` erano attributi di istanza condivisi tra il thread di polling (background) e i thread delle richieste web di Bottle. Quando due thread aprivano/usavano la connessione quasi in contemporanea, uno sovrascriveva la connessione dell'altro, causando `SQLite objects created in a thread can only be used in that same thread`. Trovato analizzando `/var/log/opc_logger.log` sulla Pi (1109 occorrenze, iniziate verso fine gennaio 2026). Questo spiegava anche perché l'auto-incremento/invio automatico al PLC a fine lavorazione si fosse fermato alla commessa 1120: l'eccezione veniva intercettata **prima** di raggiungere la chiamata a `write_tags()` nel flusso automatico. **Fix**: `conn`/`cur` ora sono proprietà backed da `threading.local()`, quindi ogni thread ha la propria connessione.

### Problema di infrastruttura risolto (non nel codice)

Il disco di `impiantoraee` (scheda SD da 6.7GB) era arrivato al **100% pieno**, causando anche il fallimento dell'installazione di Claude Code ("No space left on device"). Causa: `/var/log/opc_logger.log` (stdout del servizio, mai ruotato) aveva raggiunto **3.5GB**, gonfiato in particolare da un `print()` di debug ("Read callback") che stampa l'intero dizionario dei tag ad ogni ciclo di polling (ogni 2s). Risolto troncando i log e impostando `/etc/logrotate.d/opc_logger` (rotazione giornaliera, `copytruncate`, `maxsize 100M`, 7 rotazioni compresse).

**Da valutare**: ridurre la verbosità dei `print()` di debug in produzione (es. il dump di "Read callback" ad ogni poll) per rallentare la ricrescita del log anche tra una rotazione e l'altra.

### Punti aperti / da verificare

- **Doppie registrazioni**: l'utente ha segnalato che il server live crea talvolta record duplicati per la stessa commessa. Non ho trovato evidenza diretta nel DB attuale (solo `commessa_tx=0`, il placeholder "non iniziata", compare più volte — atteso). Sospetto una race condition strutturale: `commessa_esiste()` (check) e `insert_record()` (insert) non sono atomici, ed eseguono da thread diversi (poller vs richieste web tipo `imposta_commessa`). Se il problema si ripresenta, verificare lì — possibile fix: lock dedicato attorno a check+insert, oppure vincolo `UNIQUE` su `commessa_tx` con `INSERT OR IGNORE`.
- **Working tree molto divergente da HEAD**: l'ultimo commit Git risale a luglio 2025; `server.py`, `db.py`, `opcua_reader.py` e altri hanno modifiche sostanziali non committate. Da valutare se e quando fare un commit dello stato attuale (dopo aver verificato in produzione i fix di questa sessione).
- **`telemetria_ricostruita.db`** (il DB attivo, vedi `config.py: DATABASE_PATH`) contiene anche righe con descrizione `"Ricostruito da log - avvio lavorazione N"`, generate da `ricostruisci_db_da_log.py`: più righe `completata` per la stessa commessa sono normali lì se il lavoro è stato avviato/fermato più volte nello stesso giorno — non è un bug, non confonderlo con il punto precedente.
