#!/usr/bin/env python3
"""Stampa a video i record del database telemetria."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import TelemetriaDB
from config import DATABASE_PATH


def stampa_record(record, n):
    """Formatta una riga per la stampa."""
    ts = record.get('timestamp', '')[:19] if record.get('timestamp') else ''
    ctx = record.get('commessa_tx', '')
    stato = record.get('stato_lavorazione', '')
    e_ini = record.get('energia_iniziale_wh', 0)
    e_fin = record.get('energia_finale_wh', 0)
    e_cons = record.get('energia_consumata_wh', 0)
    pot = record.get('potenza_consumata_tx', 0)
    desc = (record.get('descrizione_commessa') or '')#[:40]
    return f"{n:4} | {ts} | {ctx:6} | {stato:14} | {e_ini:8} | {e_fin:8} | {e_cons:8} | {pot:8} | {desc}"


def main():
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            limit = 50
    if limit is None:
        limit = 100

    db_path = os.environ.get('OPC_DB_PATH', DATABASE_PATH)
    if not os.path.isabs(db_path):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_path)

    if not os.path.exists(db_path):
        print(f"Database non trovato: {db_path}")
        return 1

    db = TelemetriaDB(db_path)
    tutti = db.leggi_tutti()
    totale = len(tutti)
    records = tutti[:limit] if limit > 0 else tutti

    print(f"Database: {db_path} — {totale} record totali (mostrati {len(records)})")
    print("-" * 120)
    print(f"{'#':4} | {'timestamp':19} | {'ctx':6} | {'stato':14} | {'e_ini':8} | {'e_fin':8} | {'e_cons':8} | {'pot':8} | descrizione")
    print("-" * 120)
    for i, r in enumerate(records, 1):
        print(stampa_record(r, i))
    print("-" * 120)
    print(f"Totale: {totale} record")
    return 0


if __name__ == '__main__':
    sys.exit(main())
