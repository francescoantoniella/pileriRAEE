import sqlite3
import threading
from datetime import date, timedelta

try:
    from config import RAW_TO_KWH
except ImportError:
    RAW_TO_KWH = 100

class TelemetriaDB:
    def __init__(self, db_path='telemetria_ricostruita.db'):
        self.db_path = db_path
        self._local = threading.local()
        self.create_table()

    @property
    def conn(self):
        return getattr(self._local, 'conn', None)

    @conn.setter
    def conn(self, value):
        self._local.conn = value

    @property
    def cur(self):
        return getattr(self._local, 'cur', None)

    @cur.setter
    def cur(self, value):
        self._local.cur = value

    def open(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cur = self.conn.cursor()

    def close(self):
        if self.conn:
            self.conn.close()
        self.cur = None
        self.conn = None

    def create_table(self):
        self.open()
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS telemetria (
                timestamp TEXT PRIMARY KEY,
                commessa_rx INTEGER,
                codice_cer_rx INTEGER,
                codice_cer_tx INTEGER,
                commessa_tx INTEGER,
                ore_totali_commessa_tx INTEGER,
                minuti_totali_commessa_tx INTEGER,
                ore_lavorate_commessa_tx INTEGER,
                minuti_lavorati_commessa_tx INTEGER,
                potenza_consumata_tx INTEGER,
                descrizione_commessa TEXT,
                energia_iniziale_wh INTEGER DEFAULT 0,
                energia_finale_wh INTEGER DEFAULT 0,
                energia_consumata_wh INTEGER DEFAULT 0,
                stato_lavorazione TEXT DEFAULT 'non_iniziata'
            );
        ''')
        self.conn.commit()
        
        # Aggiungi le nuove colonne se non esistono (per database esistenti)
        new_columns = [
            ('descrizione_commessa', 'TEXT'),
            ('energia_iniziale_wh', 'INTEGER DEFAULT 0'),
            ('energia_finale_wh', 'INTEGER DEFAULT 0'),
            ('energia_consumata_wh', 'INTEGER DEFAULT 0'),
            ('stato_lavorazione', 'TEXT DEFAULT "non_iniziata"')
        ]
        
        for column_name, column_type in new_columns:
            try:
                self.cur.execute(f'ALTER TABLE telemetria ADD COLUMN {column_name} {column_type}')
                self.conn.commit()
                print(f"Colonna {column_name} aggiunta alla tabella esistente")
            except sqlite3.OperationalError:
                # La colonna esiste già, ignora l'errore
                pass
        
        self.close()

    def insert_record(self, data):
        self.open()
        self.cur.execute('''
            INSERT OR REPLACE INTO telemetria VALUES (
                :timestamp,
                :commessa_rx,
                :codice_cer_rx,
                :codice_cer_tx,
                :commessa_tx,
                :ore_totali_commessa_tx,
                :minuti_totali_commessa_tx,
                :ore_lavorate_commessa_tx,
                :minuti_lavorati_commessa_tx,
                :potenza_consumata_tx,
                :descrizione_commessa,
                :energia_iniziale_wh,
                :energia_finale_wh,
                :energia_consumata_wh,
                :stato_lavorazione
            );
        ''', {
            'timestamp': data['timestamp'],
            'commessa_rx': data['Commessa RX'],
            'codice_cer_rx': data['Codice CER RX'],
            'codice_cer_tx': data['Codice CER TX'],
            'commessa_tx': data['Commessa TX'],
            'ore_totali_commessa_tx': data['Ore totali commessa TX'],
            'minuti_totali_commessa_tx': data['Minuti totali commessa TX'],
            'ore_lavorate_commessa_tx': data['Ore lavorate commessa TX'],
            'minuti_lavorati_commessa_tx': data['Minuti lavorati commessa TX'],
            'potenza_consumata_tx': data['Potenza consumata TX'],
            'descrizione_commessa': data.get('Descrizione commessa', ''),
            'energia_iniziale_wh': data.get('energia_iniziale_wh', 0),
            'energia_finale_wh': data.get('energia_finale_wh', 0),
            'energia_consumata_wh': data.get('energia_consumata_wh', 0),
            'stato_lavorazione': data.get('stato_lavorazione', 'non_iniziata')
        })
        self.conn.commit()
        self.close()

    def aggiorna_energia_iniziale(self, commessa_rx, energia_iniziale_wh):
        """Aggiorna l'energia iniziale per una commessa specifica"""
        self.open()
        # Prima prova a trovare un record con commessa_tx = commessa_rx (aggiorna solo il più recente)
        self.cur.execute('''
            UPDATE telemetria 
            SET energia_iniziale_wh = ?, stato_lavorazione = 'in_lavorazione'
            WHERE rowid = (SELECT rowid FROM telemetria WHERE commessa_tx = ? ORDER BY timestamp DESC LIMIT 1)
        ''', (energia_iniziale_wh, commessa_rx))
        
        # Se non ha trovato record con quella commessa, cerca record con commessa_tx = 0
        # (record di preparazione) e aggiorna SOLO l'ultimo per evitare duplicati
        if self.cur.rowcount == 0:
            self.cur.execute('''
                UPDATE telemetria 
                SET energia_iniziale_wh = ?, stato_lavorazione = 'in_lavorazione', commessa_tx = ?
                WHERE rowid = (SELECT rowid FROM telemetria WHERE commessa_tx = 0 ORDER BY timestamp DESC LIMIT 1)
            ''', (energia_iniziale_wh, commessa_rx))
        
        self.conn.commit()
        self.close()

    def aggiorna_energia_finale(self, commessa_tx, energia_finale_wh):
        """Aggiorna l'energia finale e calcola la differenza per una commessa specifica"""
        self.open()
        # Prima ottieni l'energia iniziale
        self.cur.execute('''
            SELECT energia_iniziale_wh FROM telemetria 
            WHERE commessa_tx = ? AND stato_lavorazione = 'in_lavorazione'
        ''', (commessa_tx,))
        result = self.cur.fetchone()
        
        if result:
            # Caso normale: commessa in lavorazione
            energia_iniziale = result[0]
            energia_consumata = energia_finale_wh - energia_iniziale
            
            # Aggiorna il record con energia finale e calcolata
            self.cur.execute('''
                UPDATE telemetria 
                SET energia_finale_wh = ?, energia_consumata_wh = ?, stato_lavorazione = 'completata'
                WHERE commessa_tx = ? AND stato_lavorazione = 'in_lavorazione'
            ''', (energia_finale_wh, energia_consumata, commessa_tx))
            self.conn.commit()
            self.close()
            return {
                'energia_iniziale_wh': energia_iniziale,
                'energia_finale_wh': energia_finale_wh,
                'energia_consumata_wh': energia_consumata
            }
        else:
            # Caso speciale: commessa non mai stata in lavorazione
            # Cerca se esiste un record con stato 'non_iniziata'
            self.cur.execute('''
                SELECT energia_iniziale_wh FROM telemetria 
                WHERE commessa_tx = ? AND stato_lavorazione = 'non_iniziata'
                ORDER BY timestamp DESC LIMIT 1
            ''', (commessa_tx,))
            result_non_iniziata = self.cur.fetchone()
            
            if result_non_iniziata:
                energia_iniziale = result_non_iniziata[0]
                energia_consumata = energia_finale_wh - energia_iniziale
                
                # Aggiorna solo l'ultimo record con energia finale e calcolata (evita duplicati)
                self.cur.execute('''
                    UPDATE telemetria 
                    SET energia_finale_wh = ?, energia_consumata_wh = ?, stato_lavorazione = 'completata'
                    WHERE rowid = (SELECT rowid FROM telemetria WHERE commessa_tx = ? AND stato_lavorazione = 'non_iniziata' ORDER BY timestamp DESC LIMIT 1)
                ''', (energia_finale_wh, energia_consumata, commessa_tx))
                self.conn.commit()
                self.close()
                return {
                    'energia_iniziale_wh': energia_iniziale,
                    'energia_finale_wh': energia_finale_wh,
                    'energia_consumata_wh': energia_consumata
                }
            else:
                self.close()
                return None

    def leggi_ultimi(self, n=5):
        self.open()
        self.cur.execute('''
            SELECT * FROM telemetria
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (n,))
        righe = self.cur.fetchall()
        colonne = [desc[0] for desc in self.cur.description]
        risultati = [dict(zip(colonne, r)) for r in righe]
        self.close()
        return risultati

    def leggi_tutti_con_stato(self, n=50):
        """Legge tutti i record con informazioni sullo stato delle commesse"""
        self.open()
        self.cur.execute('''
            SELECT * FROM telemetria
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (n,))
        righe = self.cur.fetchall()
        colonne = [desc[0] for desc in self.cur.description]
        risultati = [dict(zip(colonne, r)) for r in righe]
        
        # Aggiungi informazioni sullo stato per ogni record
        for record in risultati:
            stato = record.get('stato_lavorazione', 'non_iniziata')
            commessa_tx = record.get('commessa_tx', 0)
            
            # Determina lo stato visivo
            if stato == 'completata':
                record['stato_visivo'] = 'Completata'
                record['badge_class'] = 'bg-success'
                record['icona'] = '✅'
            elif stato == 'in_lavorazione':
                record['stato_visivo'] = 'In Lavorazione'
                record['badge_class'] = 'bg-warning'
                record['icona'] = '🔄'
            elif stato == 'non_iniziata':
                record['stato_visivo'] = 'In Attesa'
                record['badge_class'] = 'bg-secondary'
                record['icona'] = '⏸️'
            elif stato=='preparazione':
                record['stato_visivo'] = 'In Preparazione'
                record['badge_class'] = 'bg-info'
                record['icona'] = '⏳'
            else:
                record['stato_visivo'] = 'Sconosciuto'
                record['badge_class'] = 'bg-dark'
                record['icona'] = '❓'
        
        self.close()
        return risultati

    def leggi_tutti(self):
        self.open()
        self.cur.execute('SELECT * FROM telemetria ORDER BY timestamp DESC')
        righe = self.cur.fetchall()
        colonne = [desc[0] for desc in self.cur.description]
        risultati = [dict(zip(colonne, r)) for r in righe]
        self.close()
        return risultati

    @staticmethod
    def _crea_dict_energia(commessa_tx, r):
        wh = r[0]
        return {
            'commessa_tx': commessa_tx,
            'energia_consumata_wh': wh,
            'energia_consumata_kwh': wh / RAW_TO_KWH,
            'energia_iniziale_wh': r[1],
            'energia_finale_wh': r[2],
            'progressivo_finale': r[3],
            'timestamp': r[4],
            'descrizione': r[5] or '',
            'stato_lavorazione': r[6],
        }

    def calcola_energia_commessa(self, commessa_tx):
        """Ottiene l'energia consumata per una commessa specifica (già calcolata)"""
        self.open()
        self.cur.execute('''
            SELECT energia_consumata_wh, energia_iniziale_wh, energia_finale_wh,
                   potenza_consumata_tx, timestamp, descrizione_commessa, stato_lavorazione
            FROM telemetria
            WHERE commessa_tx = ? AND stato_lavorazione = 'completata'
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (commessa_tx,))
        record = self.cur.fetchone()
        self.close()
        return self._crea_dict_energia(commessa_tx, record) if record else None

    def calcola_energia_tutte_commesse(self):
        """Ottiene l'energia consumata per tutte le commesse (già calcolata)"""
        self.open()
        self.cur.execute('''
            SELECT commessa_tx, energia_consumata_wh, energia_iniziale_wh, energia_finale_wh,
                   potenza_consumata_tx, timestamp, descrizione_commessa, stato_lavorazione
            FROM telemetria
            WHERE stato_lavorazione = 'completata'
            ORDER BY timestamp ASC
        ''')
        records = self.cur.fetchall()
        self.close()
        return [self._crea_dict_energia(r[0], r[1:]) for r in records]

    def report_giornaliero(self, data):
        """Genera un report giornaliero per la data specificata"""
        self.open()
        # Estrai solo la data dalla stringa ISO se necessario
        if 'T' in data:
            data = data.split('T')[0]
        
        self.cur.execute('''
            SELECT * FROM telemetria 
            WHERE date(timestamp) = ?
            ORDER BY timestamp DESC
        ''', (data,))
        righe = self.cur.fetchall()
        colonne = [desc[0] for desc in self.cur.description]
        risultati = [dict(zip(colonne, r)) for r in righe]
        self.close()
        return risultati

    def report_mensile(self, anno, mese):
        """Genera un report mensile per l'anno e mese specificati"""
        self.open()
        
        # Formatta anno e mese per la query
        anno_mese = f"{anno:04d}-{mese:02d}"
        
        self.cur.execute('''
            SELECT * FROM telemetria 
            WHERE strftime('%Y-%m', timestamp) = ?
            ORDER BY timestamp DESC
        ''', (anno_mese,))
        righe = self.cur.fetchall()
        colonne = [desc[0] for desc in self.cur.description]
        risultati = [dict(zip(colonne, r)) for r in righe]
        self.close()
        return risultati

    def report_annuale(self, anno):
        """Genera un report annuale per l'anno specificato"""
        self.open()
        
        self.cur.execute('''
            SELECT * FROM telemetria 
            WHERE strftime('%Y', timestamp) = ?
            ORDER BY timestamp DESC
        ''', (str(anno),))
        righe = self.cur.fetchall()
        colonne = [desc[0] for desc in self.cur.description]
        risultati = [dict(zip(colonne, r)) for r in righe]
        self.close()
        return risultati

    def statistiche_mensili(self, anno, mese):
        """Calcola statistiche mensili"""
        self.open()
        
        anno_mese = f"{anno:04d}-{mese:02d}"
        
        self.cur.execute('''
            SELECT
                COUNT(*) as totale_record,
                COUNT(DISTINCT commessa_tx) as commesse_uniche,
                SUM(ore_lavorate_commessa_tx) as ore_totali_lavorate,
                SUM(minuti_lavorati_commessa_tx) as minuti_totali_lavorati,
                SUM(energia_consumata_wh) as energia_totale_consumata,
                AVG(energia_consumata_wh) as energia_media_consumata
            FROM telemetria
            WHERE strftime('%Y-%m', timestamp) = ?
              AND stato_lavorazione = 'completata'
        ''', (anno_mese,))
        
        statistiche = self.cur.fetchone()
        self.close()

        if statistiche:
            raw_tot = statistiche[4] or 0
            raw_avg = statistiche[5] or 0
            return {
                'totale_record': statistiche[0],
                'commesse_uniche': statistiche[1],
                'ore_totali_lavorate': statistiche[2] or 0,
                'minuti_totali_lavorati': statistiche[3] or 0,
                'energia_totale_consumata': round(raw_tot / RAW_TO_KWH, 3),
                'energia_media_consumata': round(raw_avg / RAW_TO_KWH, 3),
            }
        return None

    def statistiche_annuali(self, anno):
        """Calcola statistiche annuali"""
        self.open()

        self.cur.execute('''
            SELECT
                COUNT(*) as totale_record,
                COUNT(DISTINCT commessa_tx) as commesse_uniche,
                SUM(ore_lavorate_commessa_tx) as ore_totali_lavorate,
                SUM(minuti_lavorati_commessa_tx) as minuti_totali_lavorati,
                SUM(energia_consumata_wh) as energia_totale_consumata,
                AVG(energia_consumata_wh) as energia_media_consumata
            FROM telemetria
            WHERE strftime('%Y', timestamp) = ?
              AND stato_lavorazione = 'completata'
        ''', (str(anno),))

        statistiche = self.cur.fetchone()
        self.close()

        if statistiche:
            raw_tot = statistiche[4] or 0
            raw_avg = statistiche[5] or 0
            return {
                'totale_record': statistiche[0],
                'commesse_uniche': statistiche[1],
                'ore_totali_lavorate': statistiche[2] or 0,
                'minuti_totali_lavorati': statistiche[3] or 0,
                'energia_totale_consumata': round(raw_tot / RAW_TO_KWH, 3),
                'energia_media_consumata': round(raw_avg / RAW_TO_KWH, 3),
            }
        return None

    def commessa_esiste(self, commessa_tx):
        """Verifica se esiste già un record per una commessa specifica"""
        self.open()
        self.cur.execute('''
            SELECT COUNT(*) as count FROM telemetria 
            WHERE commessa_tx = ?
        ''', (commessa_tx,))
        result = self.cur.fetchone()
        self.close()
        return result[0] > 0 if result else False

    def calcola_report_giornaliero(self, data):
        """Calcola il report energetico giornaliero"""
        self.open()
        
        # Ottieni tutte le commesse completate nella giornata
        self.cur.execute('''
            SELECT 
                commessa_tx,
                energia_iniziale_wh,
                energia_finale_wh,
                energia_consumata_wh,
                timestamp,
                descrizione_commessa
            FROM telemetria 
            WHERE DATE(timestamp) = ? AND stato_lavorazione = 'completata'
            ORDER BY timestamp ASC
        ''', (data,))
        
        commesse_completate = self.cur.fetchall()
        colonne = [desc[0] for desc in self.cur.description]
        commesse = [dict(zip(colonne, r)) for r in commesse_completate]
        
        # Calcola energia totale lavorazioni
        energia_lavorazioni = sum(c.get('energia_consumata_wh', 0) for c in commesse)

        # Calcola ore/minuti totali (sommando tutte le letture del giorno, indipendentemente dallo stato)
        self.cur.execute('''
            SELECT 
                SUM(ore_totali_commessa_tx) as ore_totali,
                SUM(minuti_totali_commessa_tx) as minuti_totali
            FROM telemetria 
            WHERE DATE(timestamp) = ?
        ''', (data,))
        tmp = self.cur.fetchone()
        ore_totali = tmp[0] or 0 if tmp else 0
        minuti_totali = tmp[1] or 0 if tmp else 0
        
        # Ottieni prima e ultima lettura della giornata
        self.cur.execute('''
            SELECT 
                MIN(potenza_consumata_tx) as prima_lettura,
                MAX(potenza_consumata_tx) as ultima_lettura,
                COUNT(*) as totale_letture
            FROM telemetria 
            WHERE DATE(timestamp) = ?
        ''', (data,))
        
        result = self.cur.fetchone()
        
        if result and result[0] is not None and result[1] is not None:
            prima_lettura = result[0]
            ultima_lettura = result[1]
            totale_letture = result[2]
            
            # Calcola energia standby
            energia_totale_giorno = ultima_lettura - prima_lettura
            energia_standby = energia_totale_giorno - energia_lavorazioni
            
            # Statistiche aggiuntive (somma delle commesse completate)
            ore_lavorazione = sum(c.get('ore_lavorate_commessa_tx', 0) for c in commesse)
            minuti_lavorazione = sum(c.get('minuti_lavorati_commessa_tx', 0) for c in commesse)
            
        else:
            prima_lettura = ultima_lettura = energia_totale_giorno = energia_standby = 0
            totale_letture = ore_lavorazione = minuti_lavorazione = 0
            ore_totali = minuti_totali = 0
        
        self.close()
        
        return {
            'data': data,
            'commesse_completate': len(commesse),
            'energia_lavorazioni_wh': energia_lavorazioni,
            'energia_lavorazioni_kwh': round(energia_lavorazioni / RAW_TO_KWH, 3),
            'energia_standby_wh': energia_standby,
            'energia_standby_kwh': round(energia_standby / RAW_TO_KWH, 3),
            'energia_totale_wh': energia_totale_giorno,
            'energia_totale_kwh': round(energia_totale_giorno / RAW_TO_KWH, 3),
            'prima_lettura_wh': prima_lettura,
            'ultima_lettura_wh': ultima_lettura,
            'totale_letture': totale_letture,
            'ore_lavorazione': ore_lavorazione,
            'minuti_lavorazione': minuti_lavorazione,
            'ore_totali': ore_totali,
            'minuti_totali': minuti_totali,
            'commesse_dettaglio': commesse
        }

    def aggiorna_dati_operativi(self, commessa_tx, new_data):
        """Aggiorna solo i dati operativi senza sovrascrivere energia iniziale e descrizione"""
        self.open()
        self.cur.execute('''
            UPDATE telemetria SET
                timestamp = ?,
                commessa_rx = ?,
                codice_cer_rx = ?,
                codice_cer_tx = ?,
                ore_totali_commessa_tx = ?,
                minuti_totali_commessa_tx = ?,
                ore_lavorate_commessa_tx = ?,
                minuti_lavorati_commessa_tx = ?,
                potenza_consumata_tx = ?
            WHERE rowid = (SELECT rowid FROM telemetria WHERE commessa_tx = ? AND stato_lavorazione = 'in_lavorazione' ORDER BY timestamp DESC LIMIT 1)
        ''', (
            new_data['timestamp'],
            new_data['Commessa RX'],
            new_data['Codice CER RX'],
            new_data['Codice CER TX'],
            new_data['Ore totali commessa TX'],
            new_data['Minuti totali commessa TX'],
            new_data['Ore lavorate commessa TX'],
            new_data['Minuti lavorati commessa TX'],
            new_data['Potenza consumata TX'],
            commessa_tx
        ))
        
        self.conn.commit()
        self.close()
        return True

    def aggiorna_descrizione_commessa(self, commessa_tx, nuova_descrizione):
        """Aggiorna la descrizione di una commessa specifica"""
        self.open()
        self.cur.execute('''
            UPDATE telemetria 
            SET descrizione_commessa = ?
            WHERE rowid = (SELECT rowid FROM telemetria WHERE commessa_tx = ? ORDER BY timestamp DESC LIMIT 1)
        ''', (nuova_descrizione, commessa_tx))
        
        self.conn.commit()
        self.close()
        return True

    def _calcola_report_intervallo(self, data_inizio, data_fine):
        """Calcola il report energetico per un intervallo [data_inizio, data_fine] (YYYY-MM-DD)."""
        self.open()

        # Commesse completate nell'intervallo
        self.cur.execute('''
            SELECT 
                commessa_tx,
                energia_iniziale_wh,
                energia_finale_wh,
                energia_consumata_wh,
                timestamp,
                descrizione_commessa
            FROM telemetria
            WHERE DATE(timestamp) BETWEEN ? AND ?
              AND stato_lavorazione = 'completata'
            ORDER BY timestamp ASC
        ''', (data_inizio, data_fine))

        righe = self.cur.fetchall()
        colonne = [desc[0] for desc in self.cur.description]
        commesse = [dict(zip(colonne, r)) for r in righe]

        energia_lavorazioni = sum(c.get('energia_consumata_wh', 0) for c in commesse)

        # Letture progressivo nell'intervallo
        self.cur.execute('''
            SELECT 
                MIN(potenza_consumata_tx) as prima_lettura,
                MAX(potenza_consumata_tx) as ultima_lettura,
                COUNT(*) as totale_letture
            FROM telemetria
            WHERE DATE(timestamp) BETWEEN ? AND ?
        ''', (data_inizio, data_fine))

        result = self.cur.fetchone()

        if result and result[0] is not None and result[1] is not None:
            prima_lettura = result[0]
            ultima_lettura = result[1]
            totale_letture = result[2]
            energia_totale = ultima_lettura - prima_lettura
            energia_standby = energia_totale - energia_lavorazioni
        else:
            prima_lettura = ultima_lettura = energia_totale = energia_standby = 0
            totale_letture = 0

        self.close()

        return {
            'intervallo': {
                'inizio': data_inizio,
                'fine': data_fine
            },
            'commesse_completate': len(commesse),
            'energia_lavorazioni_wh': energia_lavorazioni,
            'energia_lavorazioni_kwh': round(energia_lavorazioni / RAW_TO_KWH, 3),
            'energia_standby_wh': energia_standby,
            'energia_standby_kwh': round(energia_standby / RAW_TO_KWH, 3),
            'energia_totale_wh': energia_totale,
            'energia_totale_kwh': round(energia_totale / RAW_TO_KWH, 3),
            'prima_lettura_wh': prima_lettura,
            'ultima_lettura_wh': ultima_lettura,
            'totale_letture': totale_letture,
            'commesse_dettaglio': commesse
        }

    def calcola_report_settimanale(self, data_inizio, data_fine):
        """Report energetico settimanale tra due date YYYY-MM-DD (incluse)."""
        return self._calcola_report_intervallo(data_inizio, data_fine)

    def calcola_report_mensile(self, anno, mese):
        """Report energetico mensile per anno e mese (int)."""
        primo = date(anno, mese, 1)
        if mese == 12:
            prossimo = date(anno + 1, 1, 1)
        else:
            prossimo = date(anno, mese + 1, 1)
        ultimo = (prossimo - timedelta(days=1))
        return self._calcola_report_intervallo(primo.isoformat(), ultimo.isoformat())

    def calcola_report_annuale(self, anno):
        """Report energetico annuale per anno (int)."""
        data_inizio = date(anno, 1, 1).isoformat()
        data_fine = date(anno, 12, 31).isoformat()
        return self._calcola_report_intervallo(data_inizio, data_fine)
