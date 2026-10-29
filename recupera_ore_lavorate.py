#!/usr/bin/env python3
"""
Recupera dai log CSV ore/minuti delle commesse completate registrate a zero.

Il PLC espone i contatori ore della commessa N solo con CTX=N: per pochi secondi
in fase di registrazione (CRX=CTX=N) e poi a commessa chiusa (CRX=0, CTX=N).
Da settembre 2026 il logger non ha più visto la fase CRX=CTX e le ore sono rimaste
a zero nel DB. Le righe con CRX=N+1, CTX=N non si usano: i contatori possono già
essere azzerati per la commessa successiva.

Uso:
    python recupera_ore_lavorate.py                 # solo anteprima
    python recupera_ore_lavorate.py --applica       # backup del DB + correzione
"""

import argparse
import csv
import datetime
import sqlite3

from utils import apri_log_csv, file_log_csv
from config import DATABASE_PATH

COLONNE_CSV = ('Ore totali commessa TX', 'Minuti totali commessa TX',
               'Ore lavorate commessa TX', 'Minuti lavorati commessa TX')


def leggi_csv(cartella):
    righe = []
    for path in file_log_csv(cartella):
        with apri_log_csv(path) as f:
            for r in csv.DictReader(f):
                try:
                    ts = datetime.datetime.fromisoformat(r["timestamp"].rstrip("Z"))
                    righe.append((ts, int(float(r["Commessa RX"])), int(float(r["Commessa TX"])),
                                  tuple(int(float(r[c])) for c in COLONNE_CSV)))
                except (KeyError, TypeError, ValueError):
                    continue
    righe.sort()
    return righe


def ore_da_csv(righe, commessa):
    """(valori, timestamp) della prima lettura a commessa chiusa, o in registrazione; None se assente."""
    chiusa = [r for r in righe if r[1] == 0 and r[2] == commessa and any(r[3])]
    registrazione = [r for r in righe if r[1] == commessa and r[2] == commessa and any(r[3])]
    scelta = (chiusa or registrazione or [None])[0]
    return (scelta[3], scelta[0]) if scelta else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=DATABASE_PATH)
    ap.add_argument("--csv-dir", default=".")
    ap.add_argument("--da-commessa", type=int, default=1000000)
    ap.add_argument("--applica", action="store_true")
    args = ap.parse_args()

    righe = leggi_csv(args.csv_dir)
    conn = sqlite3.connect(args.db)
    records = conn.execute('''
        SELECT rowid, commessa_tx FROM telemetria
        WHERE commessa_tx >= ? AND stato_lavorazione = 'completata'
          AND COALESCE(ore_totali_commessa_tx, 0) = 0 AND COALESCE(minuti_totali_commessa_tx, 0) = 0
          AND COALESCE(ore_lavorate_commessa_tx, 0) = 0 AND COALESCE(minuti_lavorati_commessa_tx, 0) = 0
        ORDER BY commessa_tx
    ''', (args.da_commessa,)).fetchall()

    correzioni = []
    print(f"{'commessa':>9} {'totali':>7} {'lavorate':>8}  note")
    for rowid, comm in records:
        trovato = ore_da_csv(righe, comm)
        if not trovato:
            print(f"{comm:>9} {'-':>7} {'-':>8}  nessuna lettura ore nei CSV")
            continue
        (ot, mt, ol, ml), ts = trovato
        print(f"{comm:>9} {ot:>4}:{mt:02d} {ol:>5}:{ml:02d}  da lettura {ts:%Y-%m-%d %H:%M}")
        correzioni.append((ot, mt, ol, ml, rowid))

    print(f"\nCommesse da completare: {len(correzioni)}")

    if not args.applica:
        print("Anteprima: nessuna modifica. Rilanciare con --applica per scrivere.")
        return
    if not correzioni:
        return

    backup = f"{args.db}.bak-{datetime.datetime.now():%Y%m%d-%H%M%S}"
    dest = sqlite3.connect(backup)
    conn.backup(dest)
    dest.close()
    print(f"Backup: {backup}")

    with conn:
        conn.executemany('''
            UPDATE telemetria SET ore_totali_commessa_tx = ?, minuti_totali_commessa_tx = ?,
                ore_lavorate_commessa_tx = ?, minuti_lavorati_commessa_tx = ?
            WHERE rowid = ?
        ''', correzioni)
    print(f"Aggiornate {len(correzioni)} commesse.")


if __name__ == "__main__":
    main()
