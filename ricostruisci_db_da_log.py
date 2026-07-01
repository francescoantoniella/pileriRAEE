#!/usr/bin/env python3
"""
Ricostruisce il database telemetria a partire dai file di log CSV.
I log rappresentano fedelmente le letture dal PLC; questo script applica
la stessa logica degli stati (preparazione -> in_lavorazione -> completata)
in modo deterministico, producendo un DB senza duplicati.

Uso:
  python ricostruisci_db_da_log.py [--output telemetria_ricostruita.db] [--da 2026-01-01] [--a 2026-02-17]
  python ricostruisci_db_da_log.py --sostituisci   # sovrascrive telemetria.db (backup in .bak)

- I file con byte NUL (\\0) vengono letti rimuovendo i NUL per evitare _csv.Error.
- Per i log fino al 29/01/2026 viene applicata la correzione endianness (swap parole 16 bit). Dal 30/01 i valori sono già corretti.
  Disattivabile con --no-correzione-endianness.
- I valori energia_*_wh nel DB sono in unità raw del PLC; conversione in kWh: raw / RAW_TO_KWH (stessa costante di config.py).
"""

import csv
import io
import os
import re
import sys
import argparse
from datetime import datetime
# Assicura che db.py sia importabile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import TelemetriaDB
try:
    from config import RAW_TO_KWH
except ImportError:
    RAW_TO_KWH = 100


# Data limite: i log fino a questa data (inclusa) hanno endianness errata.
# Dal 30/01 in poi i valori sono già corretti, quindi NON si applica la correzione (evita valori assurdi).
DATA_FINE_ENDIANNESS_ERRATA = datetime(2026, 1, 29).date()

# Eccezioni: per questi file la correzione endianness si applica solo fino alla riga indicata (1-based, inclusa)
# Es.: in data_2026-01-27.log da riga 1514 in poi l'endianness è già corretta
RIGHE_ENDIANNESS_ERRATA_PER_FILE = {
    "data_2026-01-27.log": 1513,
}

FIELDNAMES = [
    'timestamp', 'Commessa RX', 'Codice CER RX', 'Codice CER TX',
    'Commessa TX', 'Ore totali commessa TX', 'Minuti totali commessa TX',
    'Ore lavorate commessa TX', 'Minuti lavorati commessa TX', 'Potenza consumata TX'
]


def parse_timestamp(ts_str):
    """Converte stringa timestamp in oggetto datetime per ordinamento."""
    try:
        # Accetta sia con che senza Z e frazione
        ts_str = ts_str.strip().rstrip('Z')
        if '.' in ts_str:
            return datetime.strptime(ts_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")
        return datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return None


def int_safe(val, default=0):
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return default


def correggi_endianness_energia(valore_raw, applica_correzione):
    """
    Se applica_correzione è True, applica lo swap delle due parole da 16 bit (ordine parole errato tipico in PLC):
    valore_corretto = (low16 << 16) | high16
    """
    if not applica_correzione:
        return valore_raw
    try:
        v = int(valore_raw) & 0xFFFFFFFF
        low = v & 0xFFFF
        high = (v >> 16) & 0xFFFF
        return (low << 16) | high
    except (TypeError, ValueError):
        return valore_raw


def carica_righe_da_log(filepath, correggi_endianness=True):
    """
    Carica tutte le righe da un file di log CSV.
    Rimuove i byte NUL (\x00) che possono causare _csv.Error.
    Per file con data <= 29/01/2026 applica la correzione endianness (dal 30/01 i valori sono già corretti).
    """
    rows = []
    try:
        with open(filepath, 'rb') as f:
            raw = f.read()
        # Rimuove NUL per evitare _csv.Error: line contains NUL
        raw = raw.replace(b'\x00', b'')
        text = raw.decode('utf-8', errors='replace')
    except Exception as e:
        print(f"  Attenzione: errore lettura {filepath}: {e}")
        return rows

    # Regola correzione endianness: per data o per riga (eccezioni)
    data_file = None
    m = re.search(r'data_(\d{4}-\d{2}-\d{2})\.log$', filepath)
    if m:
        try:
            data_file = datetime.strptime(m.group(1), "%Y-%m-%d").date()
        except ValueError:
            pass
    nome_file = os.path.basename(filepath)
    max_riga_endianness = RIGHE_ENDIANNESS_ERRATA_PER_FILE.get(nome_file)  # 1-based, inclusa

    reader = csv.DictReader(io.StringIO(text), fieldnames=FIELDNAMES)
    next(reader, None)  # skip header (riga 1)
    for riga_index, row in enumerate(reader):
        # Numero riga nel file (1-based): riga 1 = header, prima riga dati = 2
        numero_riga_file = 2 + riga_index
        ts = parse_timestamp(row.get('timestamp', ''))
        if ts is None:
            continue
        potenza_raw = int_safe(row.get('Potenza consumata TX'))
        if correggi_endianness:
            if max_riga_endianness is not None:
                applica = numero_riga_file <= max_riga_endianness
            else:
                applica = data_file is not None and data_file <= DATA_FINE_ENDIANNESS_ERRATA
            potenza_raw = correggi_endianness_energia(potenza_raw, applica)
        rows.append({
            'timestamp': row.get('timestamp', '').strip(),
            'ts': ts,
            'Commessa RX': int_safe(row.get('Commessa RX')),
            'Codice CER RX': int_safe(row.get('Codice CER RX')),
            'Codice CER TX': int_safe(row.get('Codice CER TX')),
            'Commessa TX': int_safe(row.get('Commessa TX')),
            'Ore totali commessa TX': int_safe(row.get('Ore totali commessa TX')),
            'Minuti totali commessa TX': int_safe(row.get('Minuti totali commessa TX')),
            'Ore lavorate commessa TX': int_safe(row.get('Ore lavorate commessa TX')),
            'Minuti lavorati commessa TX': int_safe(row.get('Minuti lavorati commessa TX')),
            'Potenza consumata TX': potenza_raw,
        })
    return rows


def trova_file_log(directory, da_data=None, a_data=None):
    """Elenco file data_YYYY-MM-DD.log nell'intervallo opzionale."""
    pattern = re.compile(r'data_(\d{4}-\d{2}-\d{2})\.log$')
    files = []
    for name in os.listdir(directory):
        m = pattern.match(name)
        if not m:
            continue
        path = os.path.join(directory, name)
        if not os.path.isfile(path):
            continue
        data_str = m.group(1)
        try:
            d = datetime.strptime(data_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        if da_data and d < da_data:
            continue
        if a_data and d > a_data:
            continue
        files.append((data_str, path))
    files.sort(key=lambda x: x[0])
    return [path for _, path in files]


def ricostruisci_record(righe_ordinate):
    """
    Applica la macchina a stati ai dati di log e restituisce la lista di record
    da inserire in telemetria (uno per lavorazione completata o avviata).
    """
    # Record in costruzione: lista di dict con stessa struttura del DB
    record_list = []
    # Ultimo record "in lavorazione" per commessa_tx (per chiudere quando arriva 0, ctx)
    open_by_ctx = {}

    last_crx, last_ctx = None, None

    for r in righe_ordinate:
        crx = r['Commessa RX']
        ctx = r['Commessa TX']
        potenza = r['Potenza consumata TX']
        ts = r['timestamp']

        # Transizione verso (crx != 0, ctx == 0): inizio lavorazione solo quando lo stato CAMBIA
        transizione_avvio = (crx != 0 and ctx == 0) and (last_ctx != 0 or last_crx != crx)
        if transizione_avvio:
            # Se avevamo già un record aperto per questa commessa, chiudilo (nuovo ciclo stesso numero)
            if crx in open_by_ctx:
                rec = open_by_ctx[crx]
                rec['energia_finale_wh'] = rec['energia_iniziale_wh']
                rec['energia_consumata_wh'] = 0
                rec['stato_lavorazione'] = 'completata'
                del open_by_ctx[crx]

            nuovo = {
                'timestamp': ts,
                'Commessa RX': crx,
                'Codice CER RX': r['Codice CER RX'],
                'Codice CER TX': r['Codice CER TX'],
                'Commessa TX': crx,
                'Ore totali commessa TX': 0,
                'Minuti totali commessa TX': 0,
                'Ore lavorate commessa TX': 0,
                'Minuti lavorati commessa TX': 0,
                'Potenza consumata TX': potenza,
                'Descrizione commessa': f"Ricostruito da log - avvio lavorazione {crx}",
                'energia_iniziale_wh': potenza,
                'energia_finale_wh': 0,
                'energia_consumata_wh': 0,
                'stato_lavorazione': 'in_lavorazione',
            }
            record_list.append(nuovo)
            open_by_ctx[crx] = nuovo
            last_crx, last_ctx = crx, ctx
            continue

        # Transizione verso (crx == 0, ctx != 0): lavorazione completata solo quando lo stato CAMBIA
        transizione_completamento = (crx == 0 and ctx != 0) and (last_crx != 0 or last_ctx != ctx)
        if transizione_completamento:
            if ctx in open_by_ctx:
                rec = open_by_ctx[ctx]
                rec['energia_finale_wh'] = potenza
                rec['energia_consumata_wh'] = potenza - rec['energia_iniziale_wh']
                rec['stato_lavorazione'] = 'completata'
                rec['timestamp'] = ts
                rec['Potenza consumata TX'] = potenza
                del open_by_ctx[ctx]
            last_crx, last_ctx = crx, ctx
            continue

        # Fase registrazione (crx == ctx != 0): aggiorna record aperto
        if crx == ctx and crx != 0:
            if crx in open_by_ctx:
                rec = open_by_ctx[crx]
                rec['timestamp'] = ts
                rec['Commessa RX'] = crx
                rec['Codice CER RX'] = r['Codice CER RX']
                rec['Codice CER TX'] = r['Codice CER TX']
                rec['Ore totali commessa TX'] = r['Ore totali commessa TX']
                rec['Minuti totali commessa TX'] = r['Minuti totali commessa TX']
                rec['Ore lavorate commessa TX'] = r['Ore lavorate commessa TX']
                rec['Minuti lavorati commessa TX'] = r['Minuti lavorati commessa TX']
                rec['Potenza consumata TX'] = potenza
        last_crx, last_ctx = crx, ctx

    # Chiudi eventuali record rimasti aperti (lavorazione non chiusa dal PLC)
    for ctx, rec in list(open_by_ctx.items()):
        rec['energia_finale_wh'] = rec.get('Potenza consumata TX', rec['energia_iniziale_wh'])
        rec['energia_consumata_wh'] = rec['energia_finale_wh'] - rec['energia_iniziale_wh']
        rec['stato_lavorazione'] = 'completata'

    return record_list


def main():
    parser = argparse.ArgumentParser(description='Ricostruisce il DB telemetria dai file di log CSV.')
    parser.add_argument('--output', '-o', default='telemetria_ricostruita.db', help='File DB in output')
    parser.add_argument('--sostituisci', action='store_true', help='Sovrascrivi telemetria.db (crea backup .bak)')
    parser.add_argument('--da', type=str, metavar='YYYY-MM-DD', help='Data inizio log (inclusa)')
    parser.add_argument('--a', type=str, metavar='YYYY-MM-DD', help='Data fine log (inclusa)')
    parser.add_argument('--directory', '-d', default=os.path.dirname(os.path.abspath(__file__)), help='Directory con data_*.log')
    parser.add_argument('--dry-run', action='store_true', help='Solo stampa statistiche, non scrivere DB')
    parser.add_argument('--no-correzione-endianness', action='store_true', help='Disabilita correzione endianness per log fino al 30/01/2026')
    args = parser.parse_args()

    if args.sostituisci:
        args.output = os.path.join(args.directory, 'telemetria.db')
        backup = args.output + '.bak'
        if os.path.exists(args.output):
            os.replace(args.output, backup)
            print(f"Backup esistente: {backup}")

    da_data = datetime.strptime(args.da, "%Y-%m-%d").date() if args.da else None
    a_data = datetime.strptime(args.a, "%Y-%m-%d").date() if args.a else None

    file_log = trova_file_log(args.directory, da_data, a_data)
    if not file_log:
        print("Nessun file di log trovato nell'intervallo.")
        return 1

    print(f"File di log da processare: {len(file_log)}")
    correggi_endianness = not args.no_correzione_endianness
    if correggi_endianness:
        print("Correzione endianness attiva per file fino al 29/01/2026.")
    tutte_righe = []
    for path in file_log:
        righe = carica_righe_da_log(path, correggi_endianness=correggi_endianness)
        tutte_righe.extend(righe)
        print(f"  {os.path.basename(path)}: {len(righe)} righe")

    if not tutte_righe:
        print("Nessuna riga valida nei log.")
        return 1

    tutte_righe.sort(key=lambda x: x['ts'])
    print(f"Totale righe ordinate: {len(tutte_righe)}")

    record_list = ricostruisci_record(tutte_righe)
    completate = sum(1 for r in record_list if r.get('stato_lavorazione') == 'completata')
    print(f"Record ricostruiti: {len(record_list)} (completate: {completate})")

    if args.dry_run:
        for i, r in enumerate(record_list[:20]):
            e = r.get('energia_consumata_wh', 0)
            kwh = e / RAW_TO_KWH
            print(f"  {i+1}: ts={r['timestamp'][:19]} ctx={r['Commessa TX']} stato={r['stato_lavorazione']} raw={e} kWh={kwh:.3f}")
        if len(record_list) > 20:
            print("  ...")
        return 0

    outpath = args.output
    if not os.path.isabs(outpath):
        outpath = os.path.join(args.directory, outpath)

    db = TelemetriaDB(outpath)
    db.create_table()

    # Per evitare conflitto su timestamp (PRIMARY KEY), usiamo il timestamp del record
    # eventualmente aggiungendo un suffisso se duplicato (stesso secondo per due record)
    seen_ts = set()
    for r in record_list:
        ts = r['timestamp']
        if ts in seen_ts:
            # Suffisso millisecondi fittizi per rendere univoco
            base = ts.replace('Z', '')
            for suffix in range(1, 1000):
                ts_uniq = f"{base}.{suffix:03d}Z"
                if ts_uniq not in seen_ts:
                    ts = ts_uniq
                    break
        seen_ts.add(ts)
        r['timestamp'] = ts

        data = {
            'timestamp': r['timestamp'],
            'Commessa RX': r['Commessa RX'],
            'Codice CER RX': r['Codice CER RX'],
            'Codice CER TX': r['Codice CER TX'],
            'Commessa TX': r['Commessa TX'],
            'Ore totali commessa TX': r['Ore totali commessa TX'],
            'Minuti totali commessa TX': r['Minuti totali commessa TX'],
            'Ore lavorate commessa TX': r['Ore lavorate commessa TX'],
            'Minuti lavorati commessa TX': r['Minuti lavorati commessa TX'],
            'Potenza consumata TX': r['Potenza consumata TX'],
            'Descrizione commessa': r.get('Descrizione commessa', ''),
            'energia_iniziale_wh': r.get('energia_iniziale_wh', 0),
            'energia_finale_wh': r.get('energia_finale_wh', 0),
            'energia_consumata_wh': r.get('energia_consumata_wh', 0),
            'stato_lavorazione': r.get('stato_lavorazione', 'non_iniziata'),
        }
        db.insert_record(data)

    print(f"Database scritto: {outpath}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
