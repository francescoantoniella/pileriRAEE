import sqlite3

class TelemetriaDB:
    def __init__(self, db_path='telemetria.db'):
        self.db_path = db_path
        self.conn = None
        self.cur = None
        self.create_table()

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
                potenza_consumata_tx INTEGER
            );
        ''')
        self.conn.commit()
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
                :potenza_consumata_tx
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
            'potenza_consumata_tx': data['Potenza consumata TX']
        })
        self.conn.commit()
        self.close()

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
        print(risultati)
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
                SUM(potenza_consumata_tx) as energia_totale_consumata,
                AVG(potenza_consumata_tx) as energia_media_consumata
            FROM telemetria 
            WHERE strftime('%Y-%m', timestamp) = ?
        ''', (anno_mese,))
        
        statistiche = self.cur.fetchone()
        self.close()
        
        if statistiche:
            return {
                'totale_record': statistiche[0],
                'commesse_uniche': statistiche[1],
                'ore_totali_lavorate': statistiche[2] or 0,
                'minuti_totali_lavorati': statistiche[3] or 0,
                'energia_totale_consumata': statistiche[4] or 0,
                'energia_media_consumata': statistiche[5] or 0
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
                SUM(potenza_consumata_tx) as energia_totale_consumata,
                AVG(potenza_consumata_tx) as energia_media_consumata
            FROM telemetria 
            WHERE strftime('%Y', timestamp) = ?
        ''', (str(anno),))
        
        statistiche = self.cur.fetchone()
        self.close()
        
        if statistiche:
            return {
                'totale_record': statistiche[0],
                'commesse_uniche': statistiche[1],
                'ore_totali_lavorate': statistiche[2] or 0,
                'minuti_totali_lavorati': statistiche[3] or 0,
                'energia_totale_consumata': statistiche[4] or 0,
                'energia_media_consumata': statistiche[5] or 0
            }
        return None
