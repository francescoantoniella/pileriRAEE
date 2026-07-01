# 📝 Gestione Descrizioni Commesse

## Panoramica

È stata aggiunta la funzionalità per gestire le descrizioni delle commesse nel sistema di telemetria. Questa funzionalità permette di:

1. **Aggiungere descrizioni** alle commesse completate
2. **Visualizzare le descrizioni** in tutte le tabelle e report
3. **Esportare le descrizioni** nei PDF
4. **Calcolare l'energia** per ogni singola commessa

## 🔋 Calcolo Energia

**Il campo `potenza_consumata_tx` contiene il PROGRESSIVO dell'energia in Wh!**

- Il campo `potenza_consumata_tx` contiene il progressivo dell'energia in Wh (Wattora)
- L'energia consumata per ogni commessa si calcola come **differenza tra progressivi**
- Formula: `Energia Commessa = Progressivo Finale - Progressivo Precedente`
- Ogni record nel database rappresenta una commessa completata con il suo progressivo

## 🆕 Nuove Funzionalità

### 1. Campo Descrizione nel Database
- Aggiunta colonna `descrizione_commessa` alla tabella `telemetria`
- Compatibile con database esistenti (migrazione automatica)

### 2. API per Gestione Descrizioni e Energia
- **POST** `/api/commessa/descrizione`
  - Parametri: `commessa_tx` (numero commessa), `descrizione` (testo)
  - Aggiorna la descrizione di una commessa esistente
- **GET** `/api/commessa/energia/<numero_commessa>`
  - Calcola l'energia consumata per una commessa specifica
  - Restituisce energia in Wh e kWh, progressivi e descrizione
- **GET** `/api/commesse/energia/tutte`
  - Calcola l'energia per tutte le commesse
  - Restituisce statistiche aggregate e top 5 commesse

### 3. Interfaccia Web Migliorata
- **Cruscotto con energia calcolata**: Mostra progressivo e energia effettiva per ogni commessa
- **Statistiche energia in tempo reale**: Energia totale, media e progressivo attuale
- **Form per gestire le descrizioni** delle commesse
- **Form per calcolare l'energia** di commesse specifiche
- **Pulsante "Aggiorna"** per statistiche in tempo reale
- **Tooltip esplicativi** per chiarire la differenza tra progressivo ed energia calcolata
- **Nota informativa** sotto la tabella con spiegazione del calcolo

### 4. Visualizzazione Migliorata
- Colonna "Descrizione" aggiunta a tutte le tabelle
- Descrizioni visibili in:
  - Pagina principale
  - Report giornaliero
  - Report mensile
  - Report annuale
  - Esportazioni PDF

## 🚀 Come Usare

### Aggiungere una Descrizione

1. **Tramite Interfaccia Web:**
   - Vai alla pagina principale
   - Trova la sezione "📝 Gestione Descrizioni Commesse"
   - Inserisci il numero della commessa
   - Inserisci la descrizione
   - Clicca "Salva Descrizione"

2. **Tramite API:**
   ```bash
   curl -X POST http://localhost/api/commessa/descrizione \
     -H "Content-Type: application/json" \
     -d '{"commessa_tx": 123, "descrizione": "Lavorazione pezzi metallici"}'
   ```

### Calcolare l'Energia per Commessa

**Opzione 1: Tramite Interfaccia Web**
- Vai alla pagina principale
- Trova la sezione "⚡ Calcolo Energia Commessa"
- Inserisci il numero della commessa e clicca "Calcola Energia"
- Oppure clicca "Calcola Tutte le Commesse" per vedere tutte le statistiche

**Opzione 2: Tramite Script**
```bash
python3 calcolo_energia.py
```

**Opzione 3: Tramite API**
```bash
# Energia di una commessa specifica
curl http://localhost/api/commessa/energia/123

# Energia di tutte le commesse
curl http://localhost/api/commesse/energia/tutte
```

Questo mostrerà:
- Energia consumata in Wh e kWh per ogni commessa
- Progressivi precedenti e finali
- Differenza calcolata (energia effettiva)
- Statistiche aggregate e top 5 commesse
- Esportazione dati in JSON

## 📊 Esempio di Output

```
📊 Energia consumata per commessa:
----------------------------------------------------------------------------------------------------
Commessa   Energia (Wh)    Energia (kWh)   Progressivo   Descrizione                      
----------------------------------------------------------------------------------------------------
123        150000         150.000        150000        Lavorazione pezzi metallici      
124        200000         200.000        350000        Assemblaggio componenti          
125        175000         175.000        525000        Controllo qualità                 
----------------------------------------------------------------------------------------------------
TOTALE      525000         525.000                    3 commesse

📈 Statistiche:
• Commesse totali: 3
• Energia totale consumata: 525000 Wh (525.000 kWh)
• Energia media per commessa: 175.000 kWh

🏆 Top 5 commesse per energia consumata:
1. Commessa 124: 200.000 kWh - Assemblaggio componenti
2. Commessa 125: 175.000 kWh - Controllo qualità
3. Commessa 123: 150.000 kWh - Lavorazione pezzi metallici

🔍 Dettagli progressivi:
--------------------------------------------------------------------------------
Commessa   Progressivo Precedente   Progressivo Finale   Differenza (Wh)   
--------------------------------------------------------------------------------
123        0                       150000              150000            
124        150000                  350000              200000            
125        350000                  525000              175000            
```

## 🔧 Modifiche Tecniche

### Database
- Aggiunta colonna `descrizione_commessa TEXT`
- Migrazione automatica per database esistenti
- Nuova funzione `aggiorna_descrizione_commessa()`
- Nuova funzione `calcola_energia_commessa()` per calcolo energia singola commessa
- Nuova funzione `calcola_energia_tutte_commesse()` per calcolo energia tutte le commesse

### Server
- Nuovo endpoint API `/api/commessa/descrizione`
- Nuovo endpoint API `/api/commessa/energia/<numero>` per calcolo energia singola commessa
- Nuovo endpoint API `/api/commesse/energia/tutte` per calcolo energia tutte le commesse
- Nuovo endpoint API `/api/energia/statistiche` per statistiche energia in tempo reale
- Aggiornamento template per mostrare descrizioni e energia calcolata
- Modifica PDF export per includere descrizioni
- Calcolo automatico energia nel cruscotto principale

### Configurazione
- Aggiunto tag "Descrizione commessa" alla lista dei tag OPC UA

## 📁 File Modificati

- `db.py` - Struttura database e funzioni
- `server.py` - API endpoint e PDF export
- `config.py` - Lista tag OPC UA
- `templates/index.tpl` - Interfaccia web
- `templates/report.tpl` - Report giornaliero
- `templates/report_mensile.tpl` - Report mensile
- `templates/report_annuale.tpl` - Report annuale

## 🆕 File Aggiunti

- `calcolo_energia.py` - Script per calcolare energia per commessa
- `DESCRIZIONI_COMMESSE.md` - Questa documentazione

## ✅ Test

Tutte le funzionalità sono state testate:
- ✅ Struttura database
- ✅ Inserimento record con descrizione
- ✅ Aggiornamento descrizioni
- ✅ API endpoint
- ✅ Interfaccia web
- ✅ Esportazione PDF

## 💡 Note Importanti

1. **Il campo `potenza_consumata_tx` contiene il PROGRESSIVO in Wh** - non l'energia consumata direttamente
2. **L'energia si calcola come differenza tra progressivi** - Progressivo Finale - Progressivo Precedente
3. **Il cruscotto mostra entrambi i valori** - Progressivo (Wh) ed Energia Calcolata (kWh)
4. **Le descrizioni sono opzionali** - il sistema funziona anche senza
5. **Compatibilità totale** - funziona con database esistenti
6. **Interfaccia intuitiva** - facile da usare tramite web con calcoli automatici
7. **Statistiche in tempo reale** - pulsante "Aggiorna" per dati sempre aggiornati
8. **Esportazione completa** - descrizioni e energia calcolata inclusi in tutti i report

## 🎯 Prossimi Passi

Per utilizzare al meglio le nuove funzionalità:

1. **Aggiungi descrizioni** alle commesse esistenti tramite l'interfaccia web
2. **Usa lo script** `calcolo_energia.py` per analizzare i consumi
3. **Esporta i dati** in JSON per analisi esterne
4. **Monitora i report** per vedere le descrizioni nei PDF

Il sistema è ora completo per la gestione delle commesse con descrizioni e calcolo automatico dell'energia!